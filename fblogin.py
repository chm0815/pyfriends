import sys, urllib, urllib2, cookielib

class FacebookLogin(object):
	def __init__(self,user,passw):
		self.user=user
		self.passw=passw
		self.browser = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
		self.browser.addheaders=[('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0')]
		urllib2.install_opener(self.browser)

	
	def login(self):
		params=urllib.urlencode({'email': self.user, 'pass': self.passw})
		#now login
		print 'Logging in to account ' + self.user
		res=self.browser.open("https://www.facebook.com/login.php?m=m&refsrc=http://m.facebook.com/home.php&refid=8", params)
		if "login" in res.url:
			print "Login failed!"
			exit(-1)
		else:
			print "Login ok!"
		res.close()
		return self.browser
		
	def logout(self):
		print 'Logging out ' + self.user
		self.browser.open("http://m.facebook.com/logout.php?h=d439564b69cfc8f1cbca42beb7726b77&t=1314710986&refid=5&ref=mfl")
		
def main():
	fblogin=FacebookLogin("<email>","<pwd>")
	fblogin.login()
	fblogin.logout()
	
if __name__ == '__main__':
	main()