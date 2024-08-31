import maadstml
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import json
from datetime import datetime
from airflow.decorators import dag, task
from flask import Flask
import sys
import tsslogging
import os
import subprocess

sys.dont_write_bytecode = True
##################################################  REST API SERVER #####################################
# This is a REST API server that will handle connections from a client
# There are two endpoints you can use to stream data to this server:
# 1. jsondataline -  You can POST a single JSONs from your client app. Your json will be streamed to Kafka topic.
# 2. jsondataarray -  You can POST JSON arrays from your client app. Your json will be streamed to Kafka topic.


######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'owner' : 'Sebastian Maurice',    
  'enabletls': 1,
  'microserviceid' : '',
  'producerid' : 'iotsolution',  
  'topics' : 'iot-raw-data', # *************** This is one of the topic you created in SYSTEM STEP 2
  'identifier' : 'TML solution',  
  'rest_port' : 9001,  # <<< ***** replace replace with port number i.e. this is listening on port 9000 
  'delay' : 7000, # << ******* 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic
  'topicid' : -999, # <<< ********* do not modify          
  'start_date': datetime (2023, 1, 1),
  'retries': 1,
    
}

######################################## DO NOT MODIFY BELOW #############################################

# Instantiate your DAG
@dag(dag_id="tml_read_RESTAPI_step_3_kafka_producetotopic_dag", default_args=default_args, tags=["tml_read_RESTAPI_step_3_kafka_producetotopic_dag"], start_date=datetime(2023, 1, 1),schedule=None,catchup=False)
def startproducingtotopic():
   def empty():
     pass
    
dag = startproducingtotopic()

VIPERTOKEN=""
VIPERHOST=""
VIPERPORT=""
    

def producetokafka(value, tmlid, identifier,producerid,maintopic,substream,args):
     inputbuf=value     
     topicid=args['topicid']
  
     # Add a 7000 millisecond maximum delay for VIPER to wait for Kafka to return confirmation message is received and written to topic 
     delay=args['delay']
     enabletls = args['enabletls']
     identifier = args['identifier']

     try:
        result=maadstml.viperproducetotopic(VIPERTOKEN,VIPERHOST,VIPERPORT,maintopic,producerid,enabletls,delay,'','', '',0,inputbuf,substream,
                                            topicid,identifier)
     except Exception as e:
        print("ERROR:",e)

def gettmlsystemsparams(**context):

    repo=tsslogging.getrepo()  
    tsslogging.tsslogit("RESTAPI producing DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
    tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")            
        
    VIPERTOKEN = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="VIPERTOKEN")
    VIPERHOST = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="VIPERHOSTPRODUCE")
    VIPERPORT = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="VIPERPORTPRODUCE")
    
    ti = context['task_instance'] 
    ti.xcom_push(key='PRODUCETYPE',value='REST')
    ti.xcom_push(key='TOPIC',value=default_args['topics'])
    ti.xcom_push(key='PORT',value=default_args['rest_port'])
    ti.xcom_push(key='IDENTIFIER',value=default_args['identifier'])

    if VIPERHOST != "":
        app = Flask(__name__)
        app.run(port=default_args['rest_port'])

        @app.route('/jsondataline', methods=['POST'])
        def storejsondataline():
          jdata = request.get_json()
          readdata(jdata)

        @app.route('/jsondataarray', methods=['POST'])
        def storejsondataarray():    
          jdata = request.get_json()
          json_array = json.load(jdata)
          for item in json_array: 
             readdata(item)
        

     #return [VIPERTOKEN,VIPERHOST,VIPERPORT]
        
def readdata(valuedata):
      args = default_args    

      # MAin Kafka topic to store the real-time data
      maintopic = args['topics']
      producerid = args['producerid']
      try:
          producetokafka(valuedata.strip(), "", "",producerid,maintopic,"",args)
          # change time to speed up or slow down data   
          #time.sleep(0.15)
      except Exception as e:
          print(e)  
          pass  
  
def startproducing(**context):
       
       fullpath=os.path.abspath(os.path.basename(__file__))  
       subprocess.run(["tmux", "new", "-d", "-s", "viper-produce-python"])
       subprocess.run(["tmux", "send-keys", "-t", "viper-produce-python", "C-c", "ENTER"])
       subprocess.run(["tmux", "send-keys", "-t", "viper-produce-python", "cd /Viper-produce", "ENTER"])
       subprocess.run(["tmux", "send-keys", "-t", "viper-produce-python", "python {} 1 {}".format(fullpath,context), "ENTER"])        
        
if __name__ == '__main__':
    
    if len(sys.argv) > 1:
       if sys.argv[1] == "1":          
         gettmlsystemsparams(sys.argv[2])