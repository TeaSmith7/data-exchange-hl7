import os
import subprocess
import json
from azure.eventhub import EventHubConsumerClient
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# initialize result eventhub
result_eventhubs = {"msgs":[],"count_file_dropped":0,"count_recdeb_ok":0,"count_recdeb_err":0,"count_redactor_ok":0,"count_redactor_err":0,
                    "count_structure_ok":0,"count_structure_err":0}

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
    global result_eventhubs
    msg = {"filename":"","message_uuid":"","eventHubName":""}
    if partition_context.eventhub_name == os.getenv("ReceiverDebatcherEventHubReceiveName"):
        data_as_str = event.body_as_str(encoding='UTF-8') # only for receiver debatcher
        data_as_json = json.loads(data_as_str)[0]['data']
        
        if 'blobUrl' in data_as_json:
            result_eventhubs['count_file_dropped']+=1
            msg["filename"] = data_as_json["blobUrl"]
            msg["eventHubName"] =partition_context.eventhub_name
                
    elif partition_context.eventhub_name == os.getenv("RedactorEventHubReceiveName"):
        data_as_str = event.body_as_str(encoding='UTF-8')
        data_as_json = json.loads(data_as_str)
        result_eventhubs['count_recdeb_ok']+=1
        if 'metadata' in data_as_json:
            msg["filename"] = data_as_json["metadata"]["provenance"]["ext_original_file_name"]
            msg["eventHubName"] =partition_context.eventhub_name
            
        if 'message_uuid' in data_as_json:
            msg["message_uuid"] = data_as_json["message_uuid"]
            
    elif partition_context.eventhub_name == os.getenv("StructureValidatorEventHubReceiveName"):
        data_as_str = event.body_as_str(encoding='UTF-8')
        data_as_json = json.loads(data_as_str)
        result_eventhubs['count_redactor_ok'] +=1
        if 'metadata' in data_as_json:
            msg["filename"] = data_as_json["metadata"]["provenance"]["ext_original_file_name"]
            msg["eventHubName"] =partition_context.eventhub_name
            
        if 'message_uuid' in data_as_json:
            msg["message_uuid"] = data_as_json["message_uuid"]
        
        
    elif partition_context.eventhub_name == os.getenv("LakeOfSegsEventHubReceiverName"):
        data_as_str = event.body_as_str(encoding='UTF-8')
        data_as_json = json.loads(data_as_str)
        result_eventhubs['count_structure_ok'] +=1
        if 'metadata' in data_as_json:
            print (data_as_json["metadata"])
            msg["filename"] = data_as_json["metadata"]["provenance"]["ext_original_file_name"]
            msg["eventHubName"] =partition_context.eventhub_name
            
        if 'message_uuid' in data_as_json:
            msg["message_uuid"] = data_as_json["message_uuid"]
        
    elif partition_context.eventhub_name == os.getenv("JsonLakeEventHubReceiverName"):
        data_as_str = event.body_as_str(encoding='UTF-8')
        data_as_json = json.loads(data_as_str)
        if 'metadata' in data_as_json:
            msg["filename"] = data_as_json["metadata"]["provenance"]["ext_original_file_name"]
            msg["eventHubName"] =partition_context.eventhub_name
            
        if 'message_uuid' in data_as_json:
            msg["message_uuid"] = data_as_json["message_uuid"]
       

    partition_context.update_checkpoint(event)
    result_eventhubs["msgs"].append(msg)
    consumer_client.close()
    
    
    

def query_eventhubs(connection_string,consumer_group, eventhub_name ):
    """ queries eventhub and updates result dictionary with event data
    """
    #global consumer_client
    global consumer_client
    consumer_client = EventHubConsumerClient.from_connection_string(conn_str=connection_string, consumer_group=consumer_group, eventhub_name=eventhub_name)
    try:
        with consumer_client:
            # start reading from end of event stream by specifying starting_position
            consumer_client.receive(on_event=process_event, starting_position="-1")
            consumer_client.close()
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

    query = "Select * FROM c.id={}".format(message_uuid)

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
        print (result_eventhubs)
if __name__=="__main__":
    main()