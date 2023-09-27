
import os
import subprocess

from azure.eventhub import EventHubConsumerClient

from azure.cosmos import CosmosClient

from dotenv import load_dotenv

# initialize result objects
result_eventhubs = {}
result_cosmosdb = {}

def upload_messages():
    """uses inhouse upload_messages.py tool to send messages through pipeline
    """
    upload_messages_cmd =r"py ..\upload-messages-py\upload_messages.py ../hl7Messages ewl0 dev"
    upload_messages = subprocess.Popen(upload_messages_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    result = upload_messages.stdout.readlines()
    if result:return True;return upload_messages.stderr

def process_event (partition_context, event):
    print ("TEA event from partition : {} and data: {} ".format(partition_context.partition_id, event))
    print ("Data : {} ".format(event.body_as_str()))
    return event.body_as_str()

def query_eventhubs(connection_string,consumer_group, eventhub_name ):
    """ queries eventhub and updates result dictionary with event data
    """
    consumerClient = EventHubConsumerClient.from_connection_string(conn_str=connection_string, consumer_group=consumer_group, eventhub_name=eventhub_name)
    print (consumerClient)
    try:
        with consumerClient:
            # start reading from end of event stream by specifying starting_position
            event_received = consumerClient.receive(on_event=process_event, starting_position="-1")
            #update results 
            result_eventhubs[eventhub_name]= event_received
            consumerClient.close()
            return
    except Exception as e:
        print (e)

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
     # load environment variables
     load_dotenv()
     # if upload was a success, continue with checking eventhubs
     if upload_messages():
        # query eventhub for receiver debatcher
        connection =  os.getenv("EventHubConnectionString")
        consumer_group =  os.getenv("EventHubConsumerGroup")
        receiver_debatcher = os.getenv("ReceiverDebatcherEventHubReceiveName")
        print (connection, consumer_group, receiver_debatcher)
        query_eventhubs(connection, consumer_group, receiver_debatcher)
        #parallel processing
        redactor_event_hub_name = os.environ("RedactorEventHubReceiveName")
        struct_validator_event_hub_name = os.environ("RedactorEventHubReceiveName")
        lake_segs_event_hub_name = os.environ("RedactorEventHubReceiveName")
        json_lake_event_hub_name = os.environ("RedactorEventHubReceiveName")
       
        event_hub_config = [{"event_hub_connection_string":connection,"consumer_group":consumer_group,"event_hub_receiver_name":redactor_event_hub_name},
                            {"event_hub_connection_string":connection,"consumer_group":consumer_group,"event_hub_receiver_name":struct_validator_event_hub_name},
                            {"event_hub_connection_string":connection,"consumer_group":consumer_group,"event_hub_receiver_name":lake_segs_event_hub_name},
                            {"event_hub_connection_string":connection,"consumer_group":consumer_group,"event_hub_receiver_name":json_lake_event_hub_name}]
       
        consumer_clients = []

        for config in event_hub_config:
            client = EventHubConsumerClient.from_connection_string(config["event_hub_connection_string"], consumer_group=config["consumer_group"],eventhub_name = config["event_hub_receiver_name"])
            consumer_clients.append(client)

        for client in consumer_clients:
            client.receive(on_event=process_event, starting_position="-1")

        
        try:
            for client in consumer_clients:
                client.run()
        except KeyboardInterrupt:
            for client in consumer_clients:
                client.close()


if __name__=="__main__":
    main()