-- Ticket Bot for Mac: a small front end for ticketbot.py.
-- It asks what you want to do, then runs the bot in a Terminal window, so you can watch it and
-- so macOS asks Terminal (not this app) for permission to click in Safari - same as running it by hand.

property appName : "Ticket Bot"
property dayNames : {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}

on run
	set appPath to POSIX path of (path to me)
	if appPath does not end with "/" then set appPath to appPath & "/"
	set supportDir to (POSIX path of (path to application support from user domain)) & "Ticket Bot/"
	set botDir to supportDir & "bot/"
	set configFile to supportDir & "config.json"

	-- Run from a copy in Application Support: the app itself may be on a read-only disk image,
	-- and your settings survive updating the app.
	do shell script "mkdir -p " & quoted form of supportDir & " && rm -rf " & quoted form of botDir & ¬
		" && cp -R " & quoted form of (appPath & "Contents/Resources/bot") & " " & quoted form of botDir & ¬
		" && (xattr -cr " & quoted form of botDir & " 2>/dev/null; true)" & ¬
		" && ([ -f " & quoted form of configFile & " ] || cp " & quoted form of (botDir & "config.example.json") & " " & quoted form of configFile & ")"

	set bot to "/bin/bash " & quoted form of (botDir & "run.sh") & " --config " & quoted form of configFile

	if not my fileExists(supportDir & ".welcomed") then
		my setupHelp()
		do shell script "touch " & quoted form of (supportDir & ".welcomed")
	end if

	set choices to {"Start - wait for the next drop", "Start - tickets drop on a different day…", "Practice run on an event link now (don't pay)", "Check the bot can see Trinity's events", "Test the alert sound", "Edit settings", "Safari setup help"}
	repeat
		try
			set nextDrop to do shell script bot & " next"
		on error errText number errNum
			if errNum is 127 then
				set answer to button returned of (display dialog "Ticket Bot needs Python 3, which is free." & return & return & ¬
					"Click Get Python, download the macOS installer, install it, then open Ticket Bot again." with title appName ¬
					buttons {"Quit", "Get Python"} default button "Get Python" with icon caution)
				if answer is "Get Python" then open location "https://www.python.org/downloads/macos/"
			else
				display dialog "Something went wrong:" & return & return & errText with title appName buttons {"Quit"} default button "Quit" with icon stop
			end if
			return
		end try

		set picked to choose from list choices with title appName with prompt nextDrop & return & return & "What do you want to do?" ¬
			default items {item 1 of choices} OK button name "Go" cancel button name "Quit"
		if picked is false then return
		set picked to item 1 of picked

		if picked is item 1 of choices then
			my startInTerminal(supportDir, botDir, "--config " & quoted form of configFile & " run")
			return
		else if picked is item 2 of choices then
			set theDay to choose from list dayNames with title appName with prompt "Which day do tickets go on sale (at 6 PM)?" OK button name "Start" cancel button name "Back"
			if theDay is not false then
				my startInTerminal(supportDir, botDir, "--config " & quoted form of configFile & " run --day " & (do shell script "echo " & quoted form of (item 1 of theDay) & " | tr A-Z a-z"))
				return
			end if
		else if picked is item 3 of choices then
			try
				set theUrl to text returned of (display dialog "Paste the Eventbrite event link. Safari will open it and the bot clicks through to checkout right away." & return & return & ¬
					"It's a practice run: don't pay." default answer "https://www.eventbrite.ca/e/" with title appName buttons {"Back", "Start"} default button "Start" cancel button "Back")
				if theUrl contains "eventbrite." and theUrl contains "/e/" then
					my startInTerminal(supportDir, botDir, "--config " & quoted form of configFile & " run --now --event-url " & quoted form of theUrl)
					return
				end if
				display dialog "That doesn't look like an Eventbrite event link (it should contain eventbrite.ca/e/...)." with title appName buttons {"OK"} default button "OK" with icon caution
			end try
		else if picked is item 4 of choices then
			set report to do shell script bot & " check 2>&1 || true"
			display dialog report with title appName buttons {"OK"} default button "OK"
		else if picked is item 5 of choices then
			do shell script bot & " test-alert >/dev/null 2>&1 &"
		else if picked is item 6 of choices then
			do shell script "open -e " & quoted form of configFile
			display dialog "Your settings are open in TextEdit. Save them (Cmd+S) before you start the bot." with title appName buttons {"OK"} default button "OK"
		else
			my setupHelp()
		end if
	end repeat
end run

-- Runs the bot in a new Terminal window. caffeinate keeps the Mac awake while it waits.
on startInTerminal(supportDir, botDir, args)
	set cmdFile to supportDir & "Ticket Bot.command"
	set cmd to "cd " & quoted form of botDir & " && clear && exec caffeinate -i /bin/bash run.sh " & args
	do shell script "printf '#!/bin/bash\\n%s\\n' " & quoted form of cmd & " > " & quoted form of cmdFile & ¬
		" && chmod +x " & quoted form of cmdFile & " && open -a Terminal " & quoted form of cmdFile
	display notification "Leave the Terminal window open until the drop. Close it to stop the bot." with title appName
end startInTerminal

on setupHelp()
	set answer to button returned of (display dialog "One-time setup:" & return & return & ¬
		"1. In Safari, log in to eventbrite.ca." & return & ¬
		"2. Safari > Settings… > Advanced: tick \"Show features for web developers\"." & return & ¬
		"3. In the Develop menu at the top, tick \"Allow JavaScript from Apple Events\"." & return & ¬
		"4. The first time the bot runs, macOS asks if Terminal may control Safari. Click OK." & return & return & ¬
		"At the drop the bot clicks Get tickets, picks 4 and clicks Check out in your Safari. You pay with Apple Pay." with title appName ¬
		buttons {"Open Safari", "OK"} default button "OK")
	if answer is "Open Safari" then do shell script "open -a Safari https://www.eventbrite.ca/"
end setupHelp

on fileExists(p)
	try
		do shell script "test -e " & quoted form of p
		return true
	on error
		return false
	end try
end fileExists
