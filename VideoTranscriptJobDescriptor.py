import os
import threading
import json
from importlib.metadata import metadata

from FileUtil import ReadJson, WriteJson

# Allowed video/audio extensions
ALLOWED_EXTENSIONS = (".mp4", ".mov", ".3gp", ".avi", ".mp3", ".wav", ".m4a")



class VideoTranscriptJobDescriptor:

    def __init__(self, folder, video_name, metadata: dict):
        self.Lock = threading.Lock()
        self.IsCompleted = False
        self.VideoName = video_name
        self.VideoProjectFolder = folder
        self.OutputFolder = folder
        self.Language = metadata['Language']
        

        self.OutputFilePath = os.path.join(self.VideoProjectFolder, f"{os.path.splitext(os.path.basename(video_name))[0]}.txt")


    def __str__(self):
        return f" project: {os.path.basename(self.VideoProjectFolder)} component: {os.path.basename(self.VideoName)} component: {self.IsCompleted}"

    def GetOutputFilePath(self):
        return os.path.join(self.OutputFolder, self.VideoProjectFolder, f"{os.path.splitext(os.path.basename(self.VideoName))[0]}.html")


    def SetOutputFolder(self, output_folder):
        self.OutputFolder = output_folder

def GenerateJobsFromVideo(video_folder) -> list[VideoTranscriptJobDescriptor]:
    # Initialize an empty dictionary to store folder names and video file paths

    jobs = []
    # Loop through subfolders and files using os.walk
    for root, dirs, f in os.walk(video_folder):
        # Filter for allowed video files in the current directory
        video_files = [f for f in f if f.lower().endswith(ALLOWED_EXTENSIONS)]
        metadata_file = "metadata.json"
        # If there are any video files in this folder, add them to the map
        if video_files:
            folder_name = os.path.basename(root)  # Get the parent folder name (just the last part of the path)
            if folder_name.lower() == "data":
                continue
            #read the metadata
            metadata_path = os.path.join(root, metadata_file)
            try:
                metadata = ReadJson(metadata_path)
            except (json.JSONDecodeError, IOError):
                metadata = {"Language": "english"}
                if not os.path.exists(metadata_path):
                    WriteJson(metadata_path,metadata)

            jobs.extend([VideoTranscriptJobDescriptor(folder_name, os.path.abspath(os.path.join(root, file)), metadata)
                         for file in video_files])

    return jobs