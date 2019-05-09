import threading
import csv
from os import listdir
from os.path import isfile, join
import urllib
from urllib.request import urlopen, Request
import lxml.html
import datetime
import os
# from bs4 import BeautifulSoup

###### CONFIG VARIABLES - Changeable Parameters

max_threads = 10
max_level = 2

#######

headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}
thread_follower_counts = [0] * max_threads
all_done = {}

def main():
  global all_done
  global max_threads
  global max_level  
  global thread_follower_counts
  seen = 0

  if not os.path.exists('LogFiles/'):
      os.makedirs('LogFiles')

  log_file = open("LogFiles/log_file_" + str(datetime.datetime.now()), "w")

  for cur_level in range(1, 1+max_level):
    cur_files = [f for f in listdir("result_output/Level" + str(cur_level-1)) if isfile("result_output/Level" + str(cur_level-1) + "/" + f)]
    if not os.path.exists('result_output/Level' + str(cur_level)):
      os.makedirs('result_output/Level' + str(cur_level))

    # Generate followers for everyone in cur_files      
    threads = [None] * max_threads  
    for f in cur_files:
      all_followers = []
      with open("result_output/Level" + str(cur_level-1) + "/" + f, mode='r') as inptr:
        reader = csv.reader(inptr)
        for row in reader:
          all_followers.append(row[0])

      follower_index = 0
      while follower_index < len(all_followers):        
        follower = all_followers[follower_index]
        try:
          # We already have followers then don't recompute
          if(not(follower in all_done)):                    
            # if we have space
            for thread_num in range(max_threads):
              if(threads[thread_num] == None or not(threads[thread_num].isAlive())):
                seen += thread_follower_counts[thread_num]
                thread_follower_counts[thread_num] = 0

                print("\nStart thread for: ", follower, " at ", str(datetime.datetime.now()))
                threads[thread_num] = threading.Thread(target=generateFollowers, args=(follower, cur_level, log_file, thread_num))
                threads[thread_num].start()
                all_done[follower] = True

                follower_index += 1
                print("Total nodes processed = ", len(all_done))
                # print("Total edges seen = ", seen)
                break
          else:
            follower_index += 1
                
        except KeyboardInterrupt:
          print("Total nodes processed = ", len(all_done))
          # print("Total edges seen = ", seen + sum(thread_follower_counts))
          raise Exception("Kill")  

    for thread_num in range(max_threads):
      if(threads[thread_num] != None):
        threads[thread_num].join()

  print("Total nodes processed = " + str(len(all_done)), file = log_file)
  print("Total edges seen = " + str(seen), file = log_file)

def generateFollowers(org, level, log_file, thread_num):
  # Open page
  link = "https://mobile.twitter.com/" + org + "/followers"  
  try:
    req = Request(link, headers=headers)
    page = urlopen(req)
    doc = lxml.html.fromstring(page.read())
    # Extract first 20 followers
    followers = doc.xpath('//span[@class="username"]/text()')[1:]
          
    # Click on Show More and continue till we get all followers
    while(True):
      try:
        link = "https://mobile.twitter.com/" + doc.xpath('//*[@id="main_content"]/div/div[2]/div/a')[0].get('href')
        req = Request(link, headers=headers)
        page = urlopen(req)
        # print(page.geturl())
        doc = lxml.html.fromstring(page.read())
        followers += doc.xpath('//span[@class="username"]/text()')[1:]
      except:
        # Exception might mean a) we have reached end or
        #                      b) some type of timeout
        # Therefore try once more to make sure we have collected all followers
        try:
          link = "https://mobile.twitter.com/" + doc.xpath('//*[@id="main_content"]/div/div[2]/div/a')[0].get('href')
          req = Request(link, headers=headers)
          page = urlopen(req)
          doc = lxml.html.fromstring(page.read())
          followers += doc.xpath('//span[@class="username"]/text()')[1:]
        except Exception as e:
          # If we had exception on the second try
          # we can be confident that we have all followers
          break
      thread_follower_counts[thread_num-1] = len(followers)

    # Write followers to file
    with open("result_output/Level" + str(level) + "/followers_" + org + ".txt", mode='w', encoding="utf-8") as outptr:
      writer = csv.writer(outptr, dialect='excel', delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
      for follower in followers:
        writer.writerow([follower, org])

    thread_follower_counts[thread_num-1] = len(followers)
    return len(followers)

  except urllib.error.HTTPError as e:
    print("User does not exist anymore: ", org, file = log_file)
    return 0

# def printPage(req):
#   page = urlopen(req)
#   soup = BeautifulSoup(page.read(), 'lxml')
#   misc = open("error.html", "w")
#   print(soup.prettify(), file = misc)
#   misc.close() 

if __name__=="__main__":
  main()