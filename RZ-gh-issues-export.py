import urllib2
import base64
import getpass
import sys

#==== globals =======
username = raw_input("username: ")
password = getpass.getpass()
organization = raw_input("org name: ")
repository = raw_input("repository: ")
server = "api.github.com"
issues_filename = ""
milestones_filename = ""
labels_filename = ""
#==== end of globals ===

## helper function for secure requests
def request(logging_context, url, body=None):
	if body:
		print "Request[%s]: %s w/ body=%s" % (logging_context, url, body)
	else :
		print "Request[%s]: %s" % (logging_context, url)
	req = urllib2.Request(url, body)
	req.add_header("Authorization", "Basic " + base64.urlsafe_b64encode("%s:%s" % (username, password)))
	req.add_header("Content-Type", "application/json")
	req.add_header("Accept", "application/json")
	return urllib2.urlopen(req)

def set_filenames(string):
	#issues
	global issues_filename
	issues_filename = "%s_issues.json" % string
	
	#milestones
	global milestones_filename
	milestones_filename = "%s_milestones.json" % string
	
	#labels
	global labels_filename
	labels_filename = "%s_labels.json" % string

def get_issues(url):
	response = request("get_issues", "%s/issues" % url)
	file = open(issues_filename, 'w')
	file.writelines(response)
	
def get_milestones(url):
	response = request("get_milestones", "%s/milestones" % url)
	file = open(milestones_filename, 'w')
	file.writelines(response)

def get_labels(url):
	response = request("get_labels", "%s/labels" % url)
	file = open(labels_filename, 'w')
	file.writelines(response)

def main():
	#set all the filenames
	set_filenames("%s_%s" % (organization, repository))
	
	#set the source url
	src_url = "https://%s/repos/%s/%s" % (server, organization, repository)
	
	#get issues
	get_issues(src_url)
	
	#get milestones
	get_milestones(src_url)
	
	#get labels
	get_labels(src_url)

if __name__ == '__main__':
	main()
