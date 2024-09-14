
import threading
import time
from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader
import time
import json
from datetime import datetime
from xml.etree.ElementTree import Element
from .models import *
from .google_patent_2 import Google_patent


metadata_registry = MetadataRegistry()
metadata_registry.registerReader('oai_dc', oai_dc_reader)

    
class DateTimeEncoder(json.JSONEncoder):
   def default(self, obj):
         if isinstance(obj, datetime):
             return obj.isoformat()  # Convertir a formato ISO 8601
         elif isinstance(obj, Element):
             return obj.text  # Convertir a texto
        

class DateTimeDecoder(json.JSONDecoder):
     def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

     def object_hook(self, dct):
        for key, value in dct.items():
            if isinstance(value, str):
                try:
                    dct[key] = datetime.fromisoformat(value)
                except ValueError:
                    pass
            return dct


def send_message(message):
    print(message)
    
    
def compare_and_save(new_records,fuente):
    record = 0
    new = 0
    for new_record in new_records:
        # Comprueba si el registro ya existe en la base de datos
        header_json = json.dumps(new_record['header'], cls=DateTimeEncoder)
        metadata_json = json.dumps(new_record['metadata'], cls=DateTimeEncoder)
        resultado = registros.objects.get_or_create(fuente = fuente, header = header_json, metadata = metadata_json)
    return resultado

def harvest_records(url):
    client = Client(url, metadata_registry)
    new_records = []
    print('aquiiiii')

    for header, metadata, _ in client.listRecords(metadataPrefix='oai_dc'):
        print(header, metadata)
        record_dict = {
            'header': {attribute: getattr(header, attribute) for attribute in dir(header) if not attribute.startswith('__')},
            'metadata': {attribute: getattr(metadata, attribute) for attribute in dir(metadata) if not attribute.startswith('__')}
        }
        print(record_dict)
        new_records.append(record_dict)

    return new_records

   
   
def start_monitoring(data_source):
    def monitor():
        monitoring = True
        while data_source.is_monitoring == monitoring:
          print("INICIANDO BUCLE PARA : "+data_source.title)
          if data_source.url == "https://patents.google.com":
               result_data = Google_patent(data_source)
               print(result_data)
          else:
            # Realizar el monitoreo de la fuente de datos aquí
            extracted_records = harvest_records(data_source.url)
            print(extracted_records)
            send_message(f"Se han extraído {len(extracted_records)} registros.")
            send_message("Comparando registros")
            compare_and_save(extracted_records, data_source)
          print(monitoring)
          estado = fuente.objects.get(id=data_source.id)
          monitoring = estado.is_monitoring  
          if monitoring:
           print("espere: "+ str(data_source.frequency))   
           time.sleep(data_source.frequency)  # Ejemplo: Esperar 1 segundo antes de la siguiente iteración
        print("bucle terminado")

    if not data_source.is_monitoring:
        data_source.is_monitoring = True
        data_source.save()

    thread = threading.Thread(target=monitor)
    thread.start()

def stop_monitoring(data_source):
    if data_source.is_monitoring:
        data_source.is_monitoring = False
        data_source.save()