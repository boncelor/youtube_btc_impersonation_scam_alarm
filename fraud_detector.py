from googleapiclient.discovery import build
import requests # to get image from the web
import shutil # to save it locally
import cv2
import numpy as np
import pytesseract
import os
from pytube import YouTube
from skimage import io
import sys

params = sys.argv

## Set up the image URL and filename

def fetch_image(image_url):
  filename = '/var/data/' + image_url.split("/")[-1]

  dirname = os.path.dirname(filename)
  if not os.path.exists(dirname):
    os.makedirs(dirname)

  # Open the url image, set stream to True, this will return the stream content.
  r = requests.get(image_url, stream = True)

  # Check if the image was retrieved successfully
  if r.status_code == 200:
    # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
    r.raw.decode_content = True
    
    # Open a local file with wb ( write binary ) permission.
    with open(filename,'wb') as f:
        shutil.copyfileobj(r.raw, f)
  else:
    print('Thumbnail Couldn\'t be retreived')



service = build('youtube', 'v3', developerKey=params[1])

# This method extracts title, description, one thumbnail and the number of views from a video id
def get_metadata(id):
  collection = service.videos().list(part= 'snippet, statistics',id = fraudulent_video_id).execute()
  title = collection['items'][0]['snippet']['title']
  channel_title = collection['items'][0]['snippet']['channelTitle']
  description = collection['items'][0]['snippet']['description']
  views = collection['items'][0]['statistics']['viewCount']
  thumbnail = collection['items'][0]['snippet']['thumbnails']['medium']['url']
  return {'title': title, 'description': description, 'thumbnail': thumbnail, 'views': views, 'channel_title': channel_title}


def download_youtube_video(id):
  video = YouTube('https://www.youtube.com/watch?v='+id)
  video.streams.filter(progressive=True, file_extension='mp4').order_by('resolution')[0].download(output_path='/var/data', filename=id)

# This method extracts all the frames or a given number of them starting from the begining of the video
def extract_frames(id, max_frames_limit=None):
  vidcap = cv2.VideoCapture('/var/data/'+id+'.mp4')
  success,image = vidcap.read()
  count = 0
  max_frames = False
  while success and not max_frames:
    cv2.imwrite("/var/data/frame%d.jpg" % count, image)     # save frame as JPEG file      
    success,image = vidcap.read()
    count += 1
    max_frames = False if max_frames_limit == None else count>=max_frames_limit



def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
#skew correction
def deskew(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray, 0, 255,
        cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h),
        flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)    
    return rotated



if __name__ == "__main__":

  fraudulent_video_id = params[2]

  metadata = get_metadata(fraudulent_video_id)

  fetch_image(metadata['thumbnail'])

  download_youtube_video(fraudulent_video_id)
  extract_frames(fraudulent_video_id, 1)


  img_thumbnail = io.imread('/var/data/mqdefault.jpg')

  deskew_thumbnail = deskew(img_thumbnail)
  gray_thumbnail = get_grayscale(deskew_thumbnail)

  img_first_frame = io.imread('/var/data/frame0.jpg')

  deskew_first_frame = deskew(img_first_frame)
  gray_first_frame = get_grayscale(deskew_first_frame)


  custom_config = r'--oem 3 --psm 6'

  thumbnail_text = pytesseract.image_to_string(gray_thumbnail, config=custom_config)
 
  first_frame_text = pytesseract.image_to_string(gray_first_frame, config=custom_config)

  string_data = " ".join([
                 metadata['title'].lower().replace("\u200b", ""),
                 metadata['channel_title'].lower().replace("\u200b", ""),
                 metadata['description'].lower().replace("\u200b", ""),
                 thumbnail_text.lower().replace("\n", " "),
                 first_frame_text.lower().replace("\n", " ")])

  print(string_data)
  # Lets be fair and asume not everyone is a scammer
  potential_giveaway_impersonation = False

  # We setup a basic list of cryptos to filter
  list_of_cryptos_to_scam_with_giveaways = ['bitcoin','btc','eth','etherum']

  # And here is a list of some celebrities i've seen impersonated
  celebrities_not_givingaway_money = ['jeff bezos', 'steve wozniak', 'chamath palihapitiya', 'elon musk']


  #And now we can evaluate if all the content is a giveaway where some celebrity is mentioned
  if ("giveaway" in string_data and
     any(crypto in string_data for crypto in list_of_cryptos_to_scam_with_giveaways) and
     any(celebrity in string_data for celebrity in celebrities_not_givingaway_money)):
     potential_giveaway_impersonation = True
     if (potential_giveaway_impersonation):
         print ("Potential impersonation detected")
     else:
         print ("Video seems fine")

