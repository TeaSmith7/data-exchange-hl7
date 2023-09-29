import os
import subprocess
import json
from azure.eventhub import EventHubConsumerClient
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# initialize result objects
result_eventhubs = {}
result_cosmosdb = {}
consumer_client = None

def upload_messages():
    """uses inhouse upload_messages.py tool to send messages through pipeline
    """
    upload_messages_cmd =r"py ..\upload-messages-py\upload_messages.py ../hl7Messages ewl0 dev"
    upload_messages = subprocess.Popen(upload_messages_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    result = upload_messages.stdout.readlines()
    if result:return True;return upload_messages.stderr

def process_event (partition_context, event):
    """processes event data 
    """
    if partition_context.eventhub_name == os.getenv("ReceiverDebatcherEventHubReceiveName"):
        data_as_str = event.body_as_str(encoding='UTF-8') # only for receiver debatcher
        data_as_json = json.loads(data_as_str)[0]['data']
        if 'blobUrl' in data_as_json:
            if data_as_json['blobUrl'].endswith("ewl0-45625_txt.txt"):
                print ("blobURL ",data_as_json['blobUrl'])
                
    else:
        print (event)
    
    

def query_eventhubs(connection_string,consumer_group, eventhub_name ):
    """ queries eventhub and updates result dictionary with event data
    """
    #global consumer_client
    consumer_client = EventHubConsumerClient.from_connection_string(conn_str=connection_string, consumer_group=consumer_group, eventhub_name=eventhub_name)
    try:
        with consumer_client:
            # start reading from end of event stream by specifying starting_position
            consumer_client.receive(on_event=process_event, starting_position="-1")
    except KeyboardInterrupt:
        print ("Receiving had stopped")

def query_cosmosdb(container_name):
    """ queries cosmosdb container passed as argument
    
    # get cosmosdb endpoint and key from .env file
    endpoint= os.getenv("CosmosDBEndpoint")
    key=os.getenv("CosmosDBKey")
    # create cosmos db instance 
    client = CosmosClient(endpoint,key)

    database_name =os.getenv("CosmosDBName")

    container = client.get_database_client(database_name).get_container_client(container_name)

    query = "Select * FROM c"

    items = list(container.query_items(query, enable_cross_partition_query=True))
    """
     
def main():
     
     # if upload was a success, continue with checking eventhubs
     if upload_messages():
        # load environment variables
        load_dotenv()
        #get environment variables from .env file
        connection =  os.getenv("EventHubConnectionString")
        receiver_debatcher_event_hub_name = os.getenv("ReceiverDebatcherEventHubReceiveName")
        redactor_event_hub_name = os.getenv("RedactorEventHubReceiveName")
        struct_validator_event_hub_name = os.getenv("StructureValidatorEventHubReceiveName")
        lake_segs_event_hub_name = os.getenv("LakeOfSegsEventHubReceiverName")
        json_lake_event_hub_name = os.getenv("JsonLakeEventHubReceiverName")

        consumer_group_receiver_debatcher =  os.getenv("ReceiverDebatcherConsumerGroup")
        consumer_group_redactor = os.getenv("RedactorConsumerGroup")
        consumer_group_structure = os.getenv("StructureValidatorConsumerGroup")
        consumer_group_lake_segs = os.getenv("LakeOfSegsConsumerGroup")
        consumer_group_json_lake = os.getenv("JsonLakeConsumerGroup")
        
        event_hub_config = [{"event_hub_connection_string":connection,"consumer_group":consumer_group_receiver_debatcher,"event_hub_receiver_name":receiver_debatcher_event_hub_name},
                            {"event_hub_connection_string":connection,"consumer_group":consumer_group_redactor,"event_hub_receiver_name":redactor_event_hub_name},
                            {"event_hub_connection_string":connection,"consumer_group":consumer_group_structure,"event_hub_receiver_name":struct_validator_event_hub_name},
                            {"event_hub_connection_string":connection,"consumer_group":consumer_group_lake_segs,"event_hub_receiver_name":lake_segs_event_hub_name},
                            {"event_hub_connection_string":connection,"consumer_group":consumer_group_json_lake,"event_hub_receiver_name":json_lake_event_hub_name}]
       
        
        for config in event_hub_config:
            # query each eventhub
            query_eventhubs(config["event_hub_connection_string"], config["consumer_group"],config["event_hub_receiver_name"])


        
if __name__=="__main__":
    main()