from google.cloud import storage
from config import bucket_name

storage_client = storage.Client()
bucket = storage_client.bucket(bucket_name)

linter_image = bucket.blob(source_blob_name) #TODO
linter_image.download_to_filename(destination_file_name) #TODO

#TODO run docker
