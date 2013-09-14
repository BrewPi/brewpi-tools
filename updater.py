#!/usr/bin/python
# Copyright 2013 BrewPi
# This file is part of BrewPi.

# BrewPi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BrewPi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with BrewPi. If not, see <http://www.gnu.org/licenses/>.

### Geo Van O, v0.9, Sep 2013

from git import *
from time import strptime

### Function used if requested branch has not been checked out
def checkout_repo(repo, branch):
	print "Attempting to checkout "+branch
	try:
		repo.git.checkout(branch)
	except: 
		print "Failed. Ack! Quitting"
	print "Success!"

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
def check_repo(repo):
        branches = repo.git.branch('-r').split('\n')
        branches = [x.lstrip(" ").strip("* ").replace("origin/","") for x in branches]
        print "\nAvailable branches in "+str(repo).split("\"")[1]+":"
	for i in enumerate(branches):
		print "[%d] %s" % i
	while (1):
		try:
			selection = int(raw_input("Enter the number of the branch you wish to update: "))
		except ValueError:
	    		print "Use the number!"
			continue
		try:
			branch = branches[selection]
		except:
			print "Not a valid selection. Try again"
			continue
		break

	try:
		local = repo.git.show(branch).split("\n")[2]
	except GitCommandError:
		choice = raw_input("You have not previously checked out this branch. Would you like to do so now? [Y/n]: ")
		if (choice is "") or (choice is "Y") or (choice is "y") or (choice is "yes") or (choice is "YES"):
			checkout_repo(repo, branch)
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
print ""
print "Most users will want to select the 'master' choice at each of the following menus."
branch = raw_input("Press enter to continue: ")

check_repo( Repo('/var/www') )
check_repo( Repo('/home/brewpi') )

