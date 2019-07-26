library(tidyverse)
library(tidytext)
library(tm)

setwd('/Users/justinpimentel/Desktop/Projects/TwilightZone/Data')
df <- read.csv('Reviews.csv', stringsAsFactors = FALSE) %>% rename(tz = TZ) 

getTop100 = function(tzType){
  textdf <- df %>% dplyr::filter(tz == tzType) %>% select(Review)
  text <- textdf[,'Review']
  docs <- Corpus(VectorSource(text))
  docs <- tm_map(docs, content_transformer(tolower))
  docs <- tm_map(docs, removeNumbers)
  docs <- tm_map(docs, removeWords, stopwords("en"))
  docs <- tm_map(docs,removeWords, c("episodes","episode"))
  docs <- tm_map(docs, removePunctuation)
  docs <- tm_map(docs, stripWhitespace)

  dtm <- TermDocumentMatrix(docs)
  m <- as.matrix(dtm)
  v <- sort(rowSums(m), decreasing = TRUE)
  d <- data.frame(word = names(v), freq = v)
  
  return(head(d,100))
}

wFreq1959 <- getTop100('tz1959') %>% mutate(TZ = 'The Twilight Zone (1959)')
wFreq1985 <- getTop100('tz1985') %>% mutate(TZ = 'The Twilight Zone (1985)')
wFreq2001 <- getTop100('tz2002') %>% mutate(TZ = 'The Twilight Zone (2002)')
wFreq2019 <- getTop100('tz2019') %>% mutate(TZ = 'The Twilight Zone (2019)')

fullWordFreq <- wFreq1959 %>% bind_rows(wFreq1985) %>% bind_rows(wFreq2001) %>% bind_rows(wFreq2019)

write.csv(fullWordFreq, 'WordFreq.csv',row.names = FALSE)