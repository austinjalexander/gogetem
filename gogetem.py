'''
--- gogetem ---

images never had a chance...

------------------------------

gogetem may be used to search for images using the Flickr API. More information may be found here: https://github.com/austinjalexander/gogetem.

Example use:

$ python gogetem.py boston 10 austinjalexander@gmail.com

Where arg1 ("apple") is the search_keyword, arg2 (1000) is the number of images to request, and arg3 ("austinjalexander@gmail.com") is the email address to notify when the task has completed.
'''

# IMPORTS
import sys
import os
import smtplib
from time import sleep
from time import time
import requests
import urllib
import numpy as np
import pandas as pd

# CONFIGURE
search_keyword = sys.argv[1]
num_of_images = int(sys.argv[2])
num_of_batches = np.ceil(np.true_divide(num_of_images,500)) # Flickr API constraint: max per page == 500

# create storage area for data and image files
try:
    os.makedirs(search_keyword)
    for i in xrange(1,int(num_of_batches)+1):
        os.makedirs(search_keyword + "/batch{}".format(i))
except:
    print "Storage area already exists for this keyword."
    print "Program paused for 10 seconds."
    print "Exit program now to prevent overwriting files."
    sleep(10)

# QUERY FLICKR PHOTO SEARCH API
for batch in xrange(1,int(num_of_batches)+1):
    print "\n", "-"*20 # output a separator
    
    rest_query = "https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key={0}&text={1}&per_page={2}&page={3}&format=json&nojsoncallback=1".format(os.environ['FLICKR_API_KEY'], search_keyword, num_of_images, batch)
    r = requests.get(rest_query)
    print ">"*5, "HTTP request status code:", r.status_code
    # if 200 isn't returned, let user know and break
    if r.status_code != 200:
        print "[An error occured with the HTTP request.]"
        break
    # otherwise
    else:
        results = r.json()
        # output an example
        print "First result from Flickr photo-search result from batch {}:".format(batch)
        print results['photos']['photo'][0]
        
        # this dataframe will store image information
        images_df = pd.DataFrame(columns=['batch', 'index', 'url'])

        # track current image index
        index = 0 

        # track time
        time0 = time()

        # loop through each result photo 
        for photo in results['photos']['photo']:

            # relevant values for creating Flickr image URLs
            # (see: https://www.flickr.com/services/api/misc.urls.html)
            farm_id = photo['farm']
            server_id = photo['server']
            photo_id = photo['id']
            secret = photo['secret']
            size = 'm' # size of image (e.g., 's' [75x75], 'm' [longest side 240])

            # Flickr image URL format
            image_url = 'https://farm{0}.staticflickr.com/{1}/{2}_{3}_{4}.'.format(farm_id, server_id, photo_id, secret, size)

            # try each of the three file-format extensions (the three suggested by Flickr), 
            # breaking after success
            for img_format in ['jpg', 'gif', 'png']:
                r = requests.get(image_url + img_format)
                if r.status_code == 200:
                    image_url += img_format
                    break

            # save image to file
            new_filename = str(index) + image_url[-4:] # filename will be index followed my image format extension
            new_filepath = "{0}/batch{1}/{2}".format(search_keyword, batch, new_filename)
            urllib.urlretrieve(image_url, new_filepath) # download image to appropriate location

            # create new record for dataframe
            new_image_df = pd.DataFrame({'batch':[str(batch)], 'index':[str(index)], 'url':[image_url]})

            # add new record to images dataframe
            images_df = pd.concat([images_df, new_image_df])

            # increment the image index on each iteration
            index += 1

        print "\ndownload time for batch {}:".format(batch), round(time() - time0, 2), "seconds"
        
        # save image data to csv file
        data_filepath = "{0}/batch{1}.csv".format(search_keyword, batch)
        images_df.to_csv(data_filepath, index=False)

# NOTIFY USER (VIA EMAIL) THAT THE TASK HAS COMPLETED
email = sys.argv[3]
num_of_files = 0
for i in xrange(1,int(num_of_batches)+1):
  num_of_files += len(os.listdir(search_keyword + "/batch{}".format(i)))

message = "Subject: gogetem downloaded {} files!".format(num_of_files)

try:
  # these details would need to changed based on your setup
  s = smtplib.SMTP('localhost', 1025)
  s.sendmail(email, [email], message)
  s.quit()
except:
  print "\nEmail failed to send."
  print "Make sure you have a SMTP server running."
  # (e.g., to test locally, $ python -m smtpd -n -c DebuggingServer localhost:1025)

