import sys
import urllib2
import json
from StringIO import StringIO
import base64
import getpass

#==== globals =======
username = raw_input("username: ")
password = getpass.getpass()
src_org = raw_input("old org name: ")
src_repo = raw_input("old repository name: ")
dest_org = raw_input("destination org name: ")
dest_repo = raw_input("destination repository name: ")
dest_url = ""
server = "api.github.com"
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

# close an issue on github
def close_issue(repourl, issuenr):
	content = json.dumps({
		"state": "closed"
	})
	response = request('close_issue', "%s/issues/%s" % (repourl, issuenr), content)
	result = response.read()
	return json.load(StringIO(result))

def create_comment(source, repourl, issuenr):
	comment_template = '**Comment by [%s](%s)**\r\n_%s_\r\n\r\n----\r\n\r\n' % (source['user']['login'], source['user']['html_url'], source['created_at'])
	comment = json.dumps({
		"body": comment_template + source['body']
	})
	response = request('create_comment', "%s/issues/%s/comments" % (repourl, issuenr), comment)
	result = response.read()
	return json.load(StringIO(result))

def get_comments_on_issue(issue):
	if issue.has_key("comments") \
	  and issue["comments"] is not None \
	  and issue["comments"] != 0:
	  	response = request("get_comments_on_issue", "%s/comments" % issue["url"])
		result = response.read()
		comments = json.load(StringIO(result))
		return comments
	else :
		return []

def import_milestones(milestones):
	for source in milestones:
		dest = json.dumps({
			"title": source["title"],
			"state": "open",
			"description": source["description"],
			"due_on": source["due_on"]})

		try:
			res = request("create_milestone", "%s/milestones" % dest_url, dest)
			data = res.read()
			res_milestone = json.load(StringIO(data))
			print "Successfully created milestone %s" % res_milestone["title"]
		except urllib2.HTTPError as e:
			print "Could not create milestone %s" % source["title"]
			print e.read()

def import_labels(labels):
	for source in labels:
		dest = json.dumps({
			"name": source["name"],
			"color": source["color"]
		})
		
		try:
			res = request("create_label", "%s/labels" % dest_url, dest)
			data = res.read()
			res_label = json.load(StringIO(data))
			print "Successfully created label %s" % res_label["name"]
		except urllib2.HTTPError as e:
			print "Could not create label %s" % source["name"]
			print e.read()
		

def get_milestones_from_repo(url):
	response = request("get_milestones", "%s/milestones?state=all" % url)
	result = response.read()
	milestones = json.load(StringIO(result))
	return milestones
		
def get_labels_from_repo(url):
	response = request("get_labels", "%s/labels" % url)
	result = response.read()
	labels = json.load(StringIO(result))
	return labels

def get_issues_from_repo(url):
	# fucking github with its ?state=all query not working
	response = request("get_open_issues", "%s/issues?state=open" % url)
	result = response.read()
	open_issues = json.load(StringIO(result))
	response = request("get_closed_issues", "%s/issues?state=closed" % url)
	result = response.read()
	closed_issues = json.load(StringIO(result))
	issues = open_issues + closed_issues
	return sorted(issues, key=lambda k: k['number'])

def import_issues(issues, dst_milestones, dst_labels):
	for source in issues:
		labels = []
		if source.has_key("labels"):
			for src_label in source["labels"]:
				name = src_label["name"]
				for dst_label in dst_labels:
					if dst_label["name"] == name:
						labels.append(name)
						break
		milestone = None
		if source.has_key("milestone") and source["milestone"] is not None:
			title = source["milestone"]["title"]
			for dst_milestone in dst_milestones:
				if dst_milestone["title"] == title:
					milestone = dst_milestone["number"]
					break

		issue_template = '<a href="%s"><img src="%s" align="left" width="96" height="96" hspace="10"></img></a> **Issue by [%s](%s)**\r\n_%s_\r\n\r\n----\r\n\r\n' % (source['user']['html_url'], source['user']['avatar_url'], source['user']['login'], source['user']['html_url'], source['created_at'])

		body = None
		if source.has_key("body") and source["body"] is not None:
			body = issue_template + source["body"]

		dest = json.dumps({
			"title": source["title"],
			"body": body,
			"milestone": milestone,
			"labels": labels,
			"state": source['state']
		})

		res = request("create_issue", "%s/issues" % dest_url, dest)
		data = res.read()
		res_issue = json.load(StringIO(data))
		for comment in get_comments_on_issue(source):
			create_comment(comment, dest_url, res_issue["number"])
		if source['state'] == 'closed':
			close_issue(dest_url, res_issue["number"])
		print "Successfully created issue %s" % res_issue["title"]
		

def main():
	global src_url
	src_url = "https://%s/repos/%s/%s" % (server, src_org, src_repo)
	
	global dest_url
	dest_url = "https://%s/repos/%s/%s" % (server, dest_org, dest_repo)
	
	#get milestones and labels to import
	milestones = get_milestones_from_repo(src_url)
	labels = get_labels_from_repo(src_url)
	import_milestones(milestones)
	import_labels(labels)

	# update references to milestones and labels that were created
	milestones = get_milestones_from_repo(dest_url)
	labels = get_labels_from_repo(dest_url)

	#import issues
	issues = get_issues_from_repo(src_url)
	import_issues(issues, milestones, labels)


if __name__ == '__main__':
	main()
