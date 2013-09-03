#!/usr/bin/python

# Need to add in: python-setuptools python-gitdb

# <Elco> some interactive menu to pick a branch, and stash changes
# <Elco> and deal with stuff git complains about
# <Elco> like not having user configured when stashing
# <Elco> and making sure the permissions are correct after update

from git import *
from time import strptime
from logging import *

### Function used to stash local changes and update a branch passed to it
def update_repo(repo, branch):
	print "Attempting to stash any local changes..."
	try:
		resp = repo.git.stash()
		print resp
	except GitCommandError as e:
		print e
		print "Unable to stash, don't want to overwrite your stuff, aborting this branch update"
		return
	try:
		print repo.git.pull('origin', branch)
	except GitCommandError as e:
		print "Error updating "+repo.git_dir
		print e
	if 'No local changes to save' not in resp:
		print "Attempting to retrieve your local changes, cross your fingers..."
		print repo.git.stash('pop')

### Funtion to be used to check most recent commit date on the repo passed to it
def check_repo(repo, branch):
	local = repo.git.show(branch).split("\n")[2]
	if ("Date" not in local):
		local = repo.git.show(branch).split("\n")[3]
	remote = repo.git.show('origin/'+branch).split("\n")[2]
	if ("Date" not in remote):
		remote = repo.git.show('origin/'+branch).split("\n")[3]
	reponame = repo.git.remote('-v').split(":")[1].split()[0]
	localdate = strptime(local[8:-6],"%a %b %d %H:%M:%S %Y")
	remotedate = strptime(remote[8:-6],"%a %b %d %H:%M:%S %Y")

	print "\nChecking for updates on "+reponame+", branch "+branch
	print "Your local copy of "+reponame+" is current as of: "+local
	print "The most current version of BrewPi for this branch is "+remote
	if localdate < remotedate:
		print "*** Your local version of "+reponame+" is out of date."
		choice = raw_input("Would you like to update this branch? [Y/n]: ")
		if (choice is "") or (choice is "Y") or (choice is "y") or (choice is "yes") or (choice is "YES"):
			update_repo(repo, branch)
	else:
		print "Your local version of "+reponame+" is good to go!"
	

print "####################################################"
print "####                                            ####"
print "####      Welcome to the BrewPi Updater!        ####"
print "####                                            ####"
print "####################################################"

print "Most users will only want to update the master branch."
branch = raw_input("What branch would you like to check? [master]: ")
if branch is "":
	branch = "master"

check_repo( Repo('/home/geo/BrewPi/brewpi-www'), branch )
check_repo( Repo('/home/geo/BrewPi/brewpi-script'), branch )
check_repo( Repo('/home/geo/BrewPi/brewpi-tools'), branch )

#except:
#print "Error downloading git repo, local files NOT updated"

