# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Application entrypoint."""

import os
import time

import log
from auth import authentication
from google.auth.transport.requests import Request
# Handle "events" from configuration
from configuration.event_handler import EventHandler as EventHandler
from configuration.spreadsheet_configuration import SpreadsheetConfiguration as Configuration
from image.image_generator import ImageGenerator as ImageGenerator
# Handles image processing
from image.image_processor import ImageProcessor as ImageProcessor
from storage.cloud_storage_handler import CloudStorageHandler as CloudStorageHandler
from storage.drive_storage_handler import DriveStorageHandler as StorageHandler
from uploader.youtube_upload import YoutubeUploader as Uploader
from uploader.youtube_upload import AssetLibraryUploader as AdsAssetUploader
from video.video_generator import VideoGenerator as VideoGenerator
# Handles video processing
from video.video_processor import VideoProcessor as VideoProcessor

logger = log.getLogger()


def main():
    # Read environment parameters
    spreadsheet_id = os.environ.get('SPREADSHEET_ID')
    gcs_bucket_name = os.environ.get('GCS_BUCKET_NAME')
    gcp_project_number = os.environ.get('GCP_PROJECT_NUMBER')
    developer_token = os.environ.get('ADS_DEVELOPER_TOKEN')
    ads_client_id = os.environ.get('ADS_CLIENT_ID')
    cloud_preview = False

    if spreadsheet_id is None:
        print('Please set environment variable SPREADSHEET_ID.')
        exit(1)
    if gcs_bucket_name:
        cloud_preview = True
        print(f"Saving image and video preview to Google Cloud Storage bucket named: {gcs_bucket_name}.")

    credentials = authentication.get_credentials_from_secret_manager(gcp_project_number)
        
    # Starts processing only after token authenticated!
    logger.info('[v2] Started processing...')

    # Dependencies
    configuration = Configuration(spreadsheet_id, credentials)
    storage = StorageHandler(configuration.get_drive_folder(), credentials)
    cloud_storage = CloudStorageHandler(gcs_bucket_name=gcs_bucket_name)
    video_processor = VideoProcessor(
        storage,
        VideoGenerator(), 
        Uploader(
            credentials, 
            AdsAssetUploader(credentials,customer_id,developer_token)),
        cloud_storage,
        cloud_preview)
    image_processor = ImageProcessor(storage, ImageGenerator(), cloud_storage, cloud_preview)

    # Handler acts as facade
    handler = EventHandler(configuration, video_processor, image_processor)

    while True:
        try:
            # Sync drive files to local tmp
            storage.update_local_files()

            # Process configuration joining threads
            handler.handle_configuration()

        except Exception as e:
            logger.error(e)

        # Sleep!
        interval = configuration.get_interval_in_minutes()
        logger.info('Sleeping for %s minutes', interval)
        time.sleep(int(interval) * 60)


if __name__ == '__main__':
    main()
