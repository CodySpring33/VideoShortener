import boto3
import os
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

class S3Handler:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        self.bucket = os.getenv('S3_BUCKET')

    def upload_file(self, file_path: str, object_name: str = None) -> str:
        """Upload a file to S3 and return its URL"""
        if object_name is None:
            object_name = os.path.basename(file_path)

        try:
            self.s3_client.upload_file(file_path, self.bucket, object_name)
            return self.generate_presigned_url(object_name)
        except ClientError as e:
            print(f"Error uploading to S3: {e}")
            raise

    def generate_presigned_url(self, object_name: str, expiration: int = 3600) -> str:
        """Generate a presigned URL for downloading"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': object_name
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            raise

    def delete_file(self, object_name: str) -> bool:
        """Delete a file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=object_name)
            return True
        except ClientError as e:
            print(f"Error deleting from S3: {e}")
            return False 