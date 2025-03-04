from google.cloud import storage

client = storage.Client()
buckets = client.list_buckets()
for bucket in buckets:
    print(bucket.name)