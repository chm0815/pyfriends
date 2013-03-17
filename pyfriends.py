# -*- coding: utf-8 -*-

from fblogin import *
from HTMLParser import HTMLParser
import sqlite3,socket,re

class OwnFriends(HTMLParser):
	def __init__(self,browser):
		HTMLParser.__init__(self)
		self.browser=browser
		self.friendslist=[]
	
	def getFriends(self):
		for i in range(ord('A'),ord('Z')+1):
			start=chr(i)
			end=start
			print "get own friends start=%s end=%s"%(start,end)
			res=self.browser.open("http://m.facebook.com/friends.php?pa&start=%s&end=%s&refid=5&ref=mfl"%(start,end))
			self.feed(res.read())
			HTMLParser.reset(self)
		print "%d own friends found!"%(len(self.friendslist))
		return self.friendslist
	
	def handle_starttag(self, tag, attrs):
		attrsdict=dict(attrs)
		if "href" in attrsdict and "name" in attrsdict:
			self.friendslist.append(attrsdict)
	
	def handle_data(self,data):
		pass

class OtherFriends(HTMLParser):
	def __init__(self,browser,personid):
		HTMLParser.__init__(self)
		self.browser=browser
		self.friendslist=[]
		self.personid=personid
	
	def getFriends(self):
		print "get friends of %s"%(self.personid)
		for i in range(10,50000,10):
			print "%d,%s"%(i,"\n" if i%100==0 else ""),
			
			for try_i in range(10):
				try:
					res=self.browser.open("http://m.facebook.com/friends/?id=%s&q&f=%d&refid=5"%(self.personid,i),timeout=5)
					restext=res.read();
					break
				except urllib2.URLError:
					print "url error retry=%d"%(try_i)
				except socket.timeout:
					print "connection problems retry=%d"%(try_i)
				#except urllib2.HTTPError as e:
				#	print "xxxxx"
				#	if e.code == 404:
				#		print "page not found -> skip!"
				#		break
						
			self.feed(restext)
			HTMLParser.reset(self)
			if "See More Friends" not in restext:
				break
		print "\n%d friends found!"%(len(self.friendslist))
		return self.friendslist
	
	def handle_starttag(self, tag, attrs):
		attrsdict=dict(attrs)
		if "href" in attrsdict and "name" in attrsdict:
			self.friendslist.append(attrsdict)
	
	def handle_data(self,data):
		pass


def sqlite_connect():
	connection = sqlite3.connect("data")
	connection.row_factory = sqlite3.Row
	cursor = connection.cursor()
	return connection,cursor

def delete_tables():
	print "delete tables"
	connection,cursor=sqlite_connect()
	cursor.execute("delete from friends")
	cursor.execute("delete from persons")
	connection.commit()
	connection.close()
	print "tables deleted"

def personid_href(url):
	rv=None
	if url.startswith("/profile"):
		idpos=url.find("id=")
		idstr=url[idpos+3:]
		qpos=idstr.find("&")
		rv=idstr[:qpos]
	return rv
	
def findPersonid(browser,url):
	personid=None
	all_friends=0
	link = "http://m.facebook.com%s" % (url)
	try:
		res=browser.open(link)
		restext=res.read()
	except urllib2.HTTPError as e:
		if e.code == 404:
			print "404 page not found! -> skip!"
			return personid,all_friends
	
		
	pattern = "All Friends \((.*?)\)"
	p = re.compile(pattern)
	m = p.search(restext)
	if m:
		dirty_num = m.groups()[0].replace(".","")
		dirty_num = dirty_num.replace(",","")
		
		all_friends = int(dirty_num)
	
	
	idpos=restext.find("subjectid=")
	if idpos >=0:
		idstr=restext[idpos+len("subjectid="):]
		#~ fp = open("a.txt","a")
		#~ fp.write(restext)
		#~ fp.close()
		qpos=min(idstr.find('"'),idstr.find('&'))
		if qpos >=0:
			personid=idstr[:qpos]
			return personid,all_friends
	#~ idpos=restext.find("?id=")
	#~ if idpos >=0:
		#~ idstr=restext[idpos+len("?id="):]
		#~ qpos=min(idstr.find('"'),idstr.find('&'))
		#~ if qpos >=0:
			#~ rv=idstr[:qpos]
			#~ return rv
	idpos=restext.find("?subject_id=")
	if idpos >=0:
		idstr=restext[idpos+len("?subject_id="):]
		#~ fp = open("a.txt","a")
		#~ fp.write(restext)
		#~ fp.close()
		qpos=min(idstr.find('"'),idstr.find('&'))
		if qpos >=0:
			personid=idstr[:qpos]
			return personid,all_friends
		
	return personid,all_friends

def save_person(href,name,connection,cursor):
	cursor.execute("select count(*) from persons where url=:url",{"url":href})
	count=cursor.fetchone()[0]
	if count==0:
		print "save person %s"%(name.encode('ascii', 'ignore'))
		cursor.execute("insert into persons values(null,?,?,?,datetime())",(href,personid_href(href),name))
		connection.commit()

def save_friends(personid,friendslist,connection,cursor,cache):
	cursor.execute("delete from friends where personid=:personid",{"personid":personid})
	friends_insert_list = []
	person_list = []
	for attrs in friendslist:
		friends_insert_list.append((attrs["href"],personid,personid_href(attrs["href"])))
		
		#save_person(attrs["href"],attrs["name"],connection,cursor)
		#cursor.execute("select count(*) from persons where url=:url",{"url":attrs["href"]})
		count = 1 if attrs["href"] in cache else 0
		print "save friend %s %s"%(attrs["name"].encode('ascii', 'ignore'),
									"(new)" if count==0 else "")
		if count==0:
			person_list.append((attrs["href"],personid_href(attrs["href"]),attrs["name"]))
			cache[attrs["href"]] = True
			
	# Blockinsert
	num_friends = len(friends_insert_list)
	#cursor.executemany("insert into friends values(?,?,?,datetime())",(attrs["href"],personid,personid_href(attrs["href"])))
	cursor.executemany("insert into friends values(?,?,?,datetime())",friends_insert_list)
	print "%d friends saved!"%(num_friends)
	
	num_new_persons = len(person_list)
	cursor.executemany("insert into persons values(null,?,?,?,datetime())",person_list)
	print "%d new persons saved!"%(num_new_persons)
	connection.commit()
	
		

def crawl(browser,person_id,connection,cursor,cache):
	otherfriends=OtherFriends(browser,person_id);
	save_friends(person_id,otherfriends.getFriends(),connection,cursor,cache)
	cursor.execute("update persons set crawltime=datetime() where personid=?",(person_id,))
	connection.commit()

def get_cache(connection,cursor):
	cache = {}
	num_persons=0
	print "creating cache..."
	for person in cursor.execute('SELECT url FROM persons'):
		cache[person["url"]] = True
		num_persons = num_persons + 1 
	
	print "%d persons cached!" % (num_persons)
	
	return cache

def main():
	if len(sys.argv)==2 and sys.argv[1]=="--delete":
		delete_tables()
		sys.exit()
	fblogin=FacebookLogin("<email>","<pwd>")
	browser=fblogin.login()	
	con,cur = sqlite_connect()
	finish = False
	cache = get_cache(con, cur)
	
	while not finish:
		finish = True
		for person in cur.execute('SELECT * FROM persons where crawltime is null order by updts asc'):
			finish = False
			personid = person["personid"]
			url = person["url"]
			name = person["name"]
			if  personid is None:
				print url
				personid,all_friends = findPersonid(browser,url)
				if personid:
					cur.execute("update persons set personid=? where url=?",(personid,url))
					con.commit()
			else:
				x,all_friends = findPersonid(browser,url)
	
			print "url=%s id=%s name=%s"%(url,personid,name.encode('ascii', 'ignore'))
			print "All friends (%d)"%(all_friends)
			if personid and all_friends > 0 and all_friends < 1900:
				crawl(browser,personid,con,cur,cache)
			else:
				cur.execute("update persons set crawltime=datetime() where url=?",(url,))
				con.commit()
	
	con.commit()
	con.close()


	fblogin.logout()

if __name__ == '__main__':
	main()

