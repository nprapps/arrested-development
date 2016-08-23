import boto

from boto.s3.connection import OrdinaryCallingFormat

def get_bucket(bucket_name):
    """
    Established a connection and gets s3 bucket
    """

    if '.' in bucket_name:
        s3 = boto.connect_s3(calling_format=OrdinaryCallingFormat())
    else:
        s3 = boto.connect_s3()

    return s3.get_bucket(bucket_name)