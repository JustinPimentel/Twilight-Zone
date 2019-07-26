import re
import os
from time import sleep
import numpy as np
import pandas as pd
from urllib import request
from datetime import datetime
from bs4 import BeautifulSoup as soup

def getPageInfo(link):
    client = request.urlopen(link)
    response = client.read()
    pageInfo = soup(response,'html.parser')
    client.close()
    return pageInfo

tzIMDB = {'tz1959': 'https://www.imdb.com/title/tt0052520/',
          'tz1985': 'https://www.imdb.com/title/tt0088634/',
          'tz2002': 'https://www.imdb.com/title/tt0318252/',
          'tz2019': 'https://www.imdb.com/title/tt2583620/'}

os.chdir('/Users/justinpimentel/Desktop/Projects/TwilightZone/Data')
###############################################################################
## SHOWS DATASET  ##
####################
shows = pd.DataFrame()

for tz in tzIMDB.values():
    pageInfo = getPageInfo(tz)

    temp = pd.DataFrame()
    title = pageInfo.h1.text.strip()
    rating = pageInfo.find('span',{'itemprop':'ratingValue'}).text

    subtitleRaw = pageInfo.find('div',{'class':'subtext'}).text.strip().split('|')
    subtitle = [re.sub('\\n','',bit.strip()) for bit in subtitleRaw]
    
    popularityRaw = pageInfo.findAll('span',{'class':'subText'})[1].text.strip()
    separatorIndex = popularityRaw.find('\n')
    popularityScore = popularityRaw[:separatorIndex]
    
    numEpisodes = pageInfo.find('span',{'class:','bp_sub_heading'}).text.split(' ')[0]
    years = re.sub('(TV Series )|(\()|(\))' , '', subtitle[3]).split('–')

    temp.loc[0,'Title'] = title + ' ('+years[0]+')'
    temp.loc[0,'TV Rating'] = subtitle[0]
    temp.loc[0,'Show Rating'] = rating
    temp.loc[0,'Popularity Score'] = popularityRaw[:separatorIndex]

    temp.loc[0,'Year Started'] = years[0]
    temp.loc[0,'Year Ended'] = years[1] if (len(years[1]) > 1) else None
    temp.loc[0,'# Episodes'] = numEpisodes
    genres = subtitle[2].split(',')
    temp.loc[0,'Genre 1'] = genres[0].strip() if genres[0] is not None else None
    temp.loc[0,'Genre 2'] = genres[1].strip() if genres[1] is not None else None
    temp.loc[0,'Genre 3'] = genres[2].strip() if genres[2] is not None else None
    
    shows = pd.concat([shows,temp])


shows = shows.reset_index(drop = True)
shows.to_csv('Shows.csv', index = False)
###############################################################################
## AWARDS DATASET  ##
#####################
awards = pd.DataFrame()

for tz in tzIMDB.values():
    awardsPageInfo = getPageInfo(tz + 'awards?ref_=tt_awd')
    
    titleRaw = awardsPageInfo.h3.text.strip().split('\n')
    title = titleRaw[0].strip() + ' ' + titleRaw[1].split('–')[0].strip() + ')'
    
    for tableIndex in range(len(awardsPageInfo.findAll('table',{'class':'awards'}))):
        
        table = awardsPageInfo.findAll('table',{'class':'awards'})[tableIndex]
        innerTemp = pd.DataFrame()
    
        rowspans = [int(row['rowspan']) for row in table.findAll('td',{'class':'title_award_outcome'})]
        awardsPageInfo.findAll('a',{'class':'event_year'})[0].text.strip()
        outcomesTemp = [bit.b.text for bit in table.findAll('td',{'class':'title_award_outcome'})]
        awardsTemp = [bit.find('span',{'class':'award_category'}).text for bit in table.findAll('td',{'class':'title_award_outcome'})]
        awardTypesTemp = [bit.contents[0].strip() for bit in table.findAll('td',{'class':'award_description'})]
        innerTemp = pd.DataFrame({'Title': title,
                                  'Year': int(awardsPageInfo.findAll('a',{'class':'event_year'})[tableIndex].text.strip()),
                                  'Outcome': pd.Series((np.repeat(outcomesTemp,rowspans))),
                                  'Award': pd.Series((np.repeat(awardsTemp,rowspans))),
                                  'Award Type': pd.Series(awardTypesTemp)})
        awards = pd.concat([awards,innerTemp])
        
        
awards = awards.reset_index(drop = True)
awards.to_csv('Awards.csv', index = False)
###############################################################################
## EPISODES DATASET  ##
#######################
def fixString(x):
    return int(re.sub('(S)|(EP)','',x))

def fixDate(x):
    return datetime.strptime(re.sub('\.','',x),'%d %b %Y').strftime('%m/%d/%Y')


episodes = pd.DataFrame()


for tz in tzIMDB.values():
    seasonPageInfo = getPageInfo(tz + 'episodes?season=1')
    numSeason = max([int(bit.text) for bit in seasonPageInfo.find('select',{'id':'bySeason'}).findAll('option')])
    
    showParts = seasonPageInfo.find('h3',{'itemprop':'name'}).text.strip().split('\n')
    show = showParts[0] + showParts[1].strip()[:5] +')'
    
    for seasonNum in range(1,numSeason + 1):
        episodePageInfo = getPageInfo(tz + 'episodes?season='+str(seasonNum))
        episodeList = episodePageInfo.find('div',{'class':'list detail eplist'})
        
        temp = pd.DataFrame()
        for episode in episodeList.findChildren(recursive=False):
            temp = pd.DataFrame({'Show':show,
                                 'Season': [episode.find('div',{'class':'image'}).findAll('div')[-1].text.split(',')[0].strip().upper()],
                                 'Episode': [episode.find('div',{'class':'image'}).findAll('div')[-1].text.split(',')[1].strip().upper()],
                                 'Rating': float(episode.find('span',{'class':'ipl-rating-star__rating'}).text) if episode.find('span',{'class':'ipl-rating-star__rating'}) is not None else None,
                                 'Name': [episode.find('a',{'itemprop':'name'}).text.strip()],
                                 'Description': [episode.find('div',{'itemprop':'description'}).text.strip()],
                                 'Airdate': [episode.find('div',{'class':'airdate'}).text.strip()]
            })
            episodes = pd.concat([episodes,temp])

episodes = episodes[episodes['Description'] != 'Know what this is about?\n Be the first one to add a plot.'].reset_index(drop = True)

episodes['Season'] = episodes['Season'].apply(fixString)
episodes['Episode'] = episodes['Episode'].apply(fixString)
episodes['Airdate'] = episodes['Airdate'].apply(fixDate)
episodes['Unique ID'] = range(1, len(episodes) + 1)
episodes.to_csv('Episodes.csv',index = False)

###############################################################################
## REVIEWS DATASET  ##
##########################
reviews = pd.DataFrame()
runCount = 0 

for tz in tzIMDB:
    noMoreData = False
    firstPageDone = False
    while noMoreData == False:
        try:
            if firstPageDone == False:
                mainPage = getPageInfo(tzIMDB[tz] + 'reviews?ref_=tt_ov_rt')
                firstPageDone = True
            else:
                key = mainPage.find('div',{'class':'load-more-data'})['data-key']
                paginationURL = tzIMDB[tz] + 'reviews/_ajax?ref_=undefined&paginationKey=' + key
                mainPage = getPageInfo(paginationURL)
            
            reviewsOfTZ = mainPage.findAll('div',{'class':'review-container'})
            for review in reviewsOfTZ:
                try: 
                    rating = float(review.find('span',{'class':'rating-other-user-rating'}).contents[-3].text)
                except:
                    rating = None
                temp = pd.DataFrame({'TZ': tz,
                                     'Num Rating': rating,
                                     'Review': [review.find('div',{'class':'text show-more__control'}).text.strip()]
                })
                reviews = pd.concat([reviews,temp])
        except:
            noMoreData = True
        
        runCount += 1
    print('Ran: ' + str(runCount) + ' times! ' + ' (' + tz +') ' )
    sleep(60)
    

reviews.reset_index(drop = True).to_csv('Reviews.csv', index = False)
