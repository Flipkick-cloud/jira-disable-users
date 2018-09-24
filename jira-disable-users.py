#!/usr/bin/python


import os
import csv
import sys
from jira import JIRA
import urllib2, json
from datetime import datetime
import dateutil.relativedelta

#Config Parameters
JiraURLDomain = 'blablabla.atlassian.net'
JiraUrlBase = 'https://' + JiraURLDomain
excludeusersfile = 'exclude-users-list.csv'
# days to expire an account
MaxUsersAgeDays = 30

##Send this to a config file
#Max users to request
# More than 100 will not work.
MaxUsersEntries = 100



## Verify if jira cli can do the Oauth dance and add headers
# This cookie belogs to "tec" user on Jira
# All of your base are belong to us! (I know this was Engrish, but this is a reminder that this cookie need to be replaced by a decent auth function)
Cookie = 'atlassian.xsrf.token=xxxxxxx'

def loadExcludeUsersList(filename):
    """
    Load file name as the following example (first line is the header):
        jirausersname,reminder
        jose,reminder 2
        jeff, IT Director
        franchico,devops
        Johnstreet,devops
        fravin,devops
    The first column of file will be the key of dict.
    
    Params:
    -------
    filename : str

    Return:
    -------
    dict
    """
    tmpdict = {}
    #Verify if filename exists
    if os.path.isfile(filename):
    # if not, return a empty dict
    # if filename it is true, load and return it as dict
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                tmpdict[row['jirausersname']] = row['reminder']
            return tmpdict
    else:
        return {}


def jiraAutenticatedRequest(url,data):
    """
    Access an URL and return the urllib2.read() with a set of headers configured
    
    Params:
    -------
    url: str

    Returns:
    -------
    urllib2
    """ 
    request = urllib2.Request(url,data)
    request.add_header('Cookie', Cookie)
    request.add_header('cache-control', ' no-cache')
    request.add_header('authority', JiraURLDomain)
    request.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36')
    request.add_header('x-requested-with', 'XMLHttpRequest')
    request.add_header('accept', 'application/json, text/javascript, */*; q=0.01')
    return request


def jiraGetUsers(startindex, maxusersentries):
    """
    Return the users description and product access date from Jira.
    Need's Jira base URL and an authenticated cookie.
    Parameters:
    ----------
    startindex : int
    maxusersentries : int
    
    Returns:
    -------
    json
    """
    url = JiraUrlBase + '/admin/rest/um/1/user/search?activeFilter=active&chrome=false&react=false&start-index=' + startindex.__str__() + '&max-results=' + maxusersentries.__str__()
    request = jiraAutenticatedRequest(url, None)
    request.add_header('referer', JiraUrlBase + '/admin/users')
    request.get_method = lambda: 'GET'    
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:     
        if e.code > 299:
            print 'urllib2.HTTPError: ', e
    except urllib2.URLError as e:
        print 'urllib2.URLError', e.args, e.message
    else:
        return json.load(response)


def jiraDisableConfluenceAccess(jirauser):
    """
    Return true after remove the Confluence access.
    Need's Jira base URL and an authenticated cookie.
    Parameters:
    ----------
    jirauser : str
    
    Returns:
    -------
    boolean
    """
    url = JiraUrlBase + '/admin/rest/um/1/user/access?username=' + jirauser + '&productId=product:confluence:conf'
    request = jiraAutenticatedRequest(url,'{"applications":["product:jira:jira-software"]}')
    request.add_header('referer', JiraUrlBase + '/admin/users/view?username=' + jirauser)
    request.add_header('Content-Type', 'application/json')
    request.get_method = lambda: 'DELETE'
    try:
        urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        print e     
        return False
    except urllib2.URLError as e:
        print e
        return False
    else:
        return True
    

def jiraDisableJiraAcess(jirauser):
    """
    Return true after remove the Jira access.
    Need's Jira base URL and an authenticated cookie.
    Parameters:
    ----------
    jirauser : str
    
    Returns:
    -------
    boolean
    """
    url = JiraUrlBase + '/admin/rest/um/1/user/access?username=' + jirauser + '&productId=product:jira:jira-software'
    request = jiraAutenticatedRequest(url,'{"applications":["product:confluence:conf"]}')
    request.add_header('referer', JiraUrlBase + '/admin/users/view?username=' + jirauser)
    request.add_header('Content-Type', 'application/json')
    request.get_method = lambda: 'DELETE'
    try:
        urllib2.urlopen(request)
    except urllib2.HTTPError as e:     
        return False
    except urllib2.URLError as e:
        print 'urllib2.URLError: ', e.message, e.reason, e.args
        return False
    else:
        return True


def jiraEnableConfluenceAccess(jiraUser):
    """
    Return true after remove the Confluence access.
    Need's Jira base URL and an authenticated cookie.
    Parameters:
    ----------
    jiraUser : str
    
    Returns:
    -------
    boolean
    """
    

def jiraEnableJiraAcess(jiraUser):
    """
    Return true after remove the Jira access.
    Need's Jira base URL and an authenticated cookie.
    Parameters:
    ----------
    jiraUser : str
    
    Returns:
    -------
    boolean
    """


def jiraDisableUsers(maxusersagedays, maxusersentries):
    """
    Disable users that doesn't access jira or confluence in the last maxusersagedays
    Parameters:
    ----------
    maxusersagedays : int
    maxusersentries : int
    """
    i = 0
    usersc = 0
    jiradisabled = 0
    confluencedisabled = 0
    excludeUsers = loadExcludeUsersList(excludeusersfile)
    while True:
        usersJson = jiraGetUsers(i*maxusersentries, maxusersentries)
        
        for user in usersJson:
            usersc = usersc + 1
            if 'productPresenceList' in user:
                
                for productPresenceList in user['productPresenceList']:
                    
                    if 'productName' in productPresenceList:
                        product = productPresenceList['productName']
                        date = productPresenceList['date']
                        lastused = datetime.now() - datetime.fromtimestamp((int(date)/1000))                        
                        #print user['name'], product,' now: ', datetime.now(), ' date: ', datetime.fromtimestamp((int(date)/1000)), ' diff: ', lastused.days
                        if (lastused.days >= maxusersagedays):
                            
                            if user['name'] in excludeUsers:
                                print 'Skipped user: ', user['name'], '| product: ', product
                                next
                            else:
                                if product == 'Confluence':
                                    jiraDisableConfluenceAccess(user['name'])
                                    confluencedisabled = confluencedisabled + 1
                                    print 'Disable confluence for: ', user['name']
                                elif product == 'Jira':
                                    jiraDisableJiraAcess(user['name'])
                                    jiradisabled = jiradisabled + 1
                                    print 'Disable Jira for: ', user['name']
                                else:
                                    print 'No action for: ', user['name'], product, lastused.days
        i = i + 1
        if len(usersJson) < maxusersentries:
            print '===\n\nTotal Jira disabled users: ', jiradisabled
            print 'Total Confluence disabled users: ', confluencedisabled
            print 'Total users verified: ', usersc
            break







# main
jiraDisableUsers(MaxUsersAgeDays,MaxUsersEntries)

