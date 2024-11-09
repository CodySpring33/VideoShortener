import boto3
from botocore.exceptions import ClientError
import os

class S3Handler:
    def __init__(self):
        # Debug print environment variables (remove in production)
        print("AWS_ACCESS_KEY_ID:", bool(os.getenv('AWS_ACCESS_KEY_ID')))
        print("AWS_SECRET_ACCESS_KEY:", bool(os.getenv('AWS_SECRET_ACCESS_KEY')))
        print("AWS_REGION:", os.getenv('AWS_REGION'))
        print("S3_BUCKET:", os.getenv('S3_BUCKET'))

        # Initialize credentials
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        self.bucket = os.getenv('S3_BUCKET')
        
        # Check for missing credentials
        missing_vars = []
        if not os.getenv('AWS_ACCESS_KEY_ID'): missing_vars.append('AWS_ACCESS_KEY_ID')
        if not os.getenv('AWS_SECRET_ACCESS_KEY'): missing_vars.append('AWS_SECRET_ACCESS_KEY')
        if not os.getenv('AWS_REGION'): missing_vars.append('AWS_REGION')
        if not os.getenv('S3_BUCKET'): missing_vars.append('S3_BUCKET')
        
        if missing_vars:
            raise ValueError(f"Missing required AWS credentials: {', '.join(missing_vars)}")

    def upload_file(self, file_path: str, object_name: str = None) -> str:
        """Upload a file to S3 and return its URL"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if object_name is None:
            object_name = os.path.basename(file_path)

        try:
            # Get file size for progress calculation
            file_size = os.path.getsize(file_path)
            
            # Configure the callback
            def upload_progress(bytes_transferred):
                progress = (bytes_transferred / file_size) * 100
                print(f"Upload progress: {progress:.1f}%")
            
            # Upload the file with progress callback
            self.s3_client.upload_file(
                file_path, 
                self.bucket, 
                object_name,
                Callback=upload_progress
            )
            
            # Generate a presigned URL that's valid for 1 hour
            url = self.generate_presigned_url(object_name)
            
            # Delete the local file after successful upload
            os.remove(file_path)
            
            return url
        except ClientError as e:
            error_msg = f"Failed to upload {file_path} to {self.bucket}/{object_name}: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)

    def generate_presigned_url(self, object_name: str, expiration: int = 3600) -> str:
        """Generate a presigned URL for downloading"""
        try:
            url = self.s3_client.generate_presigned_url(
                ClientMethod='get_object',
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