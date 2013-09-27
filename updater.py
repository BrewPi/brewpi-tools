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

import subprocess
from time import localtime, strftime
import sys
try:
	import git
except ImportError:
	print "This update script requires python-git, please install it with 'sudo apt-get install python-git"
	sys.exit(1)


### call installDependencies.sh, so commands are only defined in one place.
def installDependencies(scriptDir):
	try:
		print "Installing dependencies and fixing permissions..."
		subprocess.check_call(["sudo", "bash", scriptDir + "/installDependencies.sh"], stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError as e:
		print "I tried to execute the installDependencies.sh bash script, an error occurred. " + \
		      "Try running it from the command line in your brewpi-script dir"


### Function used if requested branch has not been checked out
def checkout_repo(repo, branch):
	print "Attempting to checkout " + branch
	try:
		repo.git.checkout(branch)
	except git.GitCommandError, e:
		print e
		print "Failed. Ack! Quitting"
		sys.exit()
	print "Success!"


### Stash any local repo changes
def stashChanges(repo):
	choice = raw_input("Would you like to stash local changes? (Required to continue) [Y/n]: ")
	if (choice is "") or (choice is "Y") or (choice is "y") or (choice is "yes") or (choice is "YES"):
		print "Attempting to stash any changes...\n"
		try:
			resp = repo.git.stash()
			print "\n" + resp + "\n"
			print "Stash successful"
			return True
		except git.GitCommandError, e:
			print e
			print "Unable to stash, don't want to overwrite your stuff, aborting this branch update"
			return False
	else:
		print "Changes are not stashed, cannot continue without stashing. Aborting update"
		return False


### Function used to stash local changes and update a branch passed to it
def update_repo(repo, branch):
	stashed = False
	repo.git.fetch('origin', branch)
	try:
		print repo.git.merge('origin/' + branch)
	except git.GitCommandError, e:
		print e
		if "Your local changes to the following files would be overwritten by merge" in str(e):
			if not stashChanges(repo):
				return False
		print "Trying to merge again..."
		try:
			print repo.git.merge('origin/' + branch)
		except git.GitCommandError, e:
			print e
			print "Sorry, cannot automatically stash/discard local changes. Aborting"
			return False

	if stashed:
		print "##################################################################"
		print "#Your local changes were in conflict with the last update of code.#"
		print "##################################################################"
		print "The conflict is:\n"
		print "-------------------------------------------------------"
		print  repo.git.stash("show", "--full-diff", "stash@{0}")
		print "-------------------------------------------------------"
		print ""
		print  ("To make merging possible, these changes were stashed." +
		        "To merge the changes back in, you can use 'git stash pop'."
		        "Only do this if you really know what you are doing!" +
		        "Your changes might be incompatible with the update or could cause a new merge conflict.")
	print branch + " updated!"
	return True


### Function to be used to check most recent commit date on the repo passed to it
def check_repo(repo):
	updated = False
	repo.git.fetch("--prune")
	localBranch = repo.active_branch.name
	remoteBranch = ""
	remoteRef = None

	print "You are currently on branch " + localBranch

	### Get available branches on the remote
	remoteBranches = repo.remotes.origin.refs
	remoteBranches.pop(0)  # remove HEAD from list

	print "\nAvailable branches on the remote for " + repo.working_tree_dir + ":"
	for i, ref in enumerate(remoteBranches):
		remoteRefName = "%s" % ref
		remoteBranchName = remoteRefName.lstrip("origin/")
		if remoteBranchName == localBranch:
			remoteRef = ref
		print "[%d] %s" % (i, remoteBranchName)
	print "[" + str(len(remoteBranches)) + "] Skip"

	while 1:
		try:
			choice = raw_input("Enter the number of the branch you wish to update [%s]:" % localBranch)
			if choice == "":
				print "Keeping current branch %s" % localBranch
				break
			else:
				selection = int(choice)
		except ValueError:
			print "Use the number!"
			continue
		if selection == len(remoteBranches):
			return False
		try:
			remoteRef = remoteBranches[selection]
		except IndexError:
			print "Not a valid selection. Try again"
			continue
		break

	remoteBranch = ("%s" % remoteRef).lstrip("origin/")

	if localBranch != remoteBranch:
		choice = raw_input("You chose " + remoteBranch + " but it is not your currently active branch - " +
		                   "would you like me to check it out for you now? (Required to continue) [Y/n]: ")
		if (choice is "") or (choice is "Y") or (choice is "y") or (choice is "yes") or (choice is "YES"):
			try:
				print repo.git.checkout(remoteBranch)
				print "Successfully switched to " + remoteBranch
				updated = True
			except git.GitCommandError, e:
				if "Your local changes to the following files would be overwritten by checkout" in str(e):
					print "Local changes exist in your current files that need to be stashed to continue"
					if not stashChanges(repo):
						return
					print "Trying to checkout again..."
				try:
					print repo.git.checkout(remoteBranch)
					print "Checkout successful"
				except git.GitCommandError, e:
					print e
					print "I was unable to checkout. Please try it manually from the command line and re-run this tool"
					return False
		else:
			print "Skipping this branch"
			return False

	if remoteRef is None:
		print "Error: Could not determine which remote reference to use, aborting"
		exit(1)

	localDate = repo.head.commit.committed_date
	localDateString = strftime("%a, %d %b %Y %H:%M:%S", localtime(localDate))
	localSha = repo.head.commit.hexsha
	localName = repo.working_tree_dir

	remoteDate = remoteRef.commit.committed_date
	remoteDateString = strftime("%a, %d %b %Y %H:%M:%S", localtime(remoteDate))
	remoteSha = remoteRef.commit.hexsha
	remoteName = remoteRef.name
	alignLength = max(len(localName), len(remoteName))

	print "The latest commit in " + localName.ljust(alignLength) + " is " + localSha + " on " + localDateString
	print "The latest commit on " + remoteName.ljust(alignLength) + " is " + remoteSha + " on " + remoteDateString

	if localDate < remoteDate:
		print "*** Updates are available! ****"
		choice = raw_input("Would you like to update " + localName + " from " + remoteName + " [Y/n]: ")
		if (choice is "") or (choice is "Y") or (choice is "y") or (choice is "yes") or (choice is "YES"):
			updated = update_repo(repo, branch)
	else:
		print "Your local version of " + localName + " is up to date!"
	return updated

print "####################################################"
print "####                                            ####"
print "####      Welcome to the BrewPi Updater!        ####"
print "####                                            ####"
print "####################################################"
print ""
print "Most users will want to select the 'master' choice at each of the following menus."
branch = raw_input("Press enter to continue... ")

changed = False
scriptPath = '/home/brewpi'
webPath = '/var/www'

print "\n\n*** Updating BrewPi script repository ***"
for i in range(3):
	correctRepo = False
	try:
		git.Repo(scriptPath)
        except git.NoSuchPathError:
                print "The path %s does not exist" % scriptPath
                scriptPath = raw_input("What path did you install the BrewPi python scripts to? ")
		continue
        except git.InvalidGitRepositoryError:
                print "The path %s does not seem to be a valid git repository" % scriptPath
                scriptPath = raw_input("What path did you install the BrewPi python scripts to? ")
		continue
        try:
                gitConfig = open(scriptPath+'/.git/config', 'r')
                for line in gitconfig:
                        if "url = https://github.com/BrewPi/brewpi-script.git" in line:
                                correctRepo = True
                                break
                gitConfig.close()
	if not correctRepo:
		print "The path %s does not seem to be the BrewPi python script git repository" % scriptPath
		scriptPath = raw_input("What path did you install the BrewPi python scripts to? ")
		continue
	try:
		changed = check_repo(git.Repo(scriptPath)) or changed
	else:
		break
else:
	print "Maximum number of tries reached, updating BrewPi scripts aborted"

print "\n\n*** Updating BrewPi web interface repository ***"
for i in range(3):
	correctRepo = False
        try:
                git.Repo(webPath)
        except git.NoSuchPathError:
                print "The path %s does not exist" % webPath
                webPath = raw_input("What path did you install the BrewPi web interface scripts to? ")
		continue
        except git.InvalidGitRepositoryError:
                print "The path %s does not seem to be a valid git repository" % webPath
                webPath = raw_input("What path did you install the BrewPi web interface scripts to? ")
		continue
	try:
		gitConfig = open(webPath+'/.git/config', 'r')
		for line in gitconfig:
			if "url = https://github.com/BrewPi/brewpi-www.git" in line:
				correctRepo = True
				break
		gitConfig.close()
	if not correctRepo:
                print "The path %s does not seem to be the BrewPi web interface git repository" % webPath
                webPath = raw_input("What path did you install the BrewPi web interface scripts to? ")
		continue
        try:
                changed = check_repo(git.Repo(webPath)) or changed
        else:
                break
else:
	print "Maximum number of tries reached, updating BrewPi web interface aborted"

if changed:
	installDependencies(scriptPath)

print "\n\n*** Done updating BrewPi! ***"
