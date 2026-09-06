#!/usr/bin/python3
import abc, sys, os, platform, shutil, time, pathlib, binascii

VERSION = "v2.1"

def prgood(content):
	# print(f"[\033[0;32m✓\033[0m] {content}")
	# so that people aren't confused by the [?]. stupid Windows.
	print(f"[\033[0;32mOK\033[0m] {content}")

def prbad(content):
	print(f"[\033[0;91mXX\033[0m] {content}")

def prinfo(content):
	print(f"[--] {content}")


osver = platform.system()
thisfile = os.path.abspath(__file__)
scriptroot = os.path.dirname(thisfile)
systmp = None

def exitOnEnter(errCode = 0):
	if osver == "Linux":
		os.sync()

	input("[--] Press Enter to exit...")
	exit(errCode)

def need_hangul_fix():
	if osver == "Darwin":
		return True
	if osver == "Linux":
		uname = os.uname()
		# iSH
		if uname.machine == "i686" and uname.release.endswith("-ish"):
			return True
	return False

def verify_device():
	def throw_error():
		prbad("Error 01: Script is not running on your SD card!")
		prinfo(f"Current location: {scriptroot}")
		exitOnEnter()
	# check for aShell on iOS/iPadOS
	if osver == "Darwin" and os.uname().machine.startswith(("iPod", "iPhone", "iPad")):  # safe to ignore AppleTV or Apple Watch ?
		if "com.apple.filesystems.userfsd" not in os.getcwd():
			throw_error()
	# for the rest
	else:
		systemroot = pathlib.Path(sys.executable).anchor # Never hardcode C:. My Windows drive letter is E:, my SD card or USB drive is often C:.
		if os.stat(scriptroot).st_dev == os.stat(systemroot).st_dev:
			throw_error()

def dig_for_root():
	global thisfile, scriptroot

	if not os.path.ismount(scriptroot):
		root = scriptroot
		while not os.path.ismount(root) and root != os.path.dirname(root):
			root = os.path.dirname(root)

		for f in ["SafeB9S.bin", "b9", "boot.firm", "boot.3dsx", "boot9strap/", "mset9.py", "MSET9-Windows.bat", "MSET9-macOS.command", "_INSTRUCTIONS.txt", "errors.txt"]:
			try:
				shutil.move(os.path.join(scriptroot, f), os.path.join(root, f))
			except:
				pass # The sanity checks will deal with that. I just don't want the exception to terminate the script.

		with open(os.path.join(scriptroot, "Note from MSET9.txt"), "w") as f:
			f.write("Hey!\n")
			f.write("All the MSET9 files have been moved to the root of your SD card.\n\n")

			f.write("\"What is the 'root of my SD card'...?\"\n")
			f.write("The root is 'not inside any folder'.\n")
			f.write("This is where you can see your 'Nintendo 3DS' folder. (It is not inside the Nintendo 3DS folder itself!)\n\n")

			f.write("Reference image: https://3ds.hacks.guide/images/screenshots/onboarding/sdroot.png\n\n")

			f.write(f"At the time of writing, the root of your SD card is at: '{root}'. Check it out!\n")
			f.close()

		scriptroot = root
		thisfile = os.path.join(scriptroot, "mset9.py")

def try_chdir():
	global scriptroot
	try:
		os.chdir(scriptroot)
	except Exception as exc:
		# prbad("Error 08: Couldn't reapply working directory, is SD card reinserted?") Wasn't in the troubleshooting section, doesn't really need a number IMO
		prbad("Failed to change directory to SD card. is it inserted?")
		prbad(f"Error details: {str(exc)}")
		exitOnEnter()

def is_writable():
	global scriptroot
	writable = os.access(scriptroot, os.W_OK)
	try: # Bodge for windows
		with open("test.txt", "w") as f:
			f.write("test")
			f.close()
		os.remove("test.txt")
	except:
		writable = False
	return writable

def abs(path):
	global scriptroot
	return os.path.join(scriptroot, path)

def fix_hangul(name):
	cho_base = 0x1100
	is_cho = lambda c: c >= cho_base and c <= 0x1112
	jung_base = 0x1161
	is_jung = lambda c: c >= jung_base and c <= 0x1175
	jong_base = 0x11A8
	is_jong = lambda c: c >= jong_base and c <= 0x11C2
	new_str = ""
	syllable_code = 0;
	def append_syllable():
		nonlocal new_str, syllable_code
		new_str += chr(syllable_code + 44032)
		syllable_code = 0
	for char in name:
		code = ord(char)
		if is_cho(code):
			if syllable_code != 0:
				append_syllable()
			syllable_code += (code - cho_base) * 588
		elif is_jung(code):
			syllable_code += (code - jung_base) * 28
		elif is_jong(code):
			syllable_code += code - jong_base + 1  # this one start with 1
		else:
			if syllable_code != 0:
				append_syllable()
			new_str += char
	return new_str


verify_device()
dig_for_root()
try_chdir()

def clearScreen():
	if osver == "Windows":
		os.system("cls")
	else:
		os.system("clear")

# -1: Cancelled
def getInput(options):
	if type(options) == range:
		options = [*options, (options[-1] + 1)]

	while 1:
		try:
			opt = int(input(">>> "))
		except KeyboardInterrupt:
			print()
			return -1
		except EOFError:
			print()
			return -1
		except ValueError:
			opt = 0xFFFFFFFF

		if opt not in options:
			prbad(f"Invalid input, try again. Valid inputs: {str.join(', ', (str(i) for i in options))}")
			continue

		return opt

# Section: insureRoot
if not os.path.exists(abs("Nintendo 3DS/")):
	prbad("Error 01: Nintendo 3DS folder not found!")
	prinfo(f"Current location: {scriptroot}")
	print()

	prinfo("How to generate the Nintendo 3DS folder:")
	prinfo("1. Safely eject your SD card from your PC.")
	prinfo("2. Insert your SD card into your 3DS.")
	prinfo("3. Power on your 3DS, and wait for it to reach the HOME menu.")
	prinfo("4. Press the POWER button to turn off your 3DS.")
	prinfo("5. Re-insert your SD card into your PC.")
	prinfo("The Nintendo 3DS folder should appear on the SD card.")
	print()
	prinfo("If the folder still does not appear, or your 3DS complains that the SD card")
	prinfo("could not be detected/could not be accessed, you may need to format the SD card to FAT32.")
	prinfo("Consult: https://wiki.hacks.guide/wiki/Formatting_an_SD_card")

	exitOnEnter()

# Section: sdWritable
def writeProtectCheck():
	prinfo("Checking if SD card is writeable...")
	if not is_writable():
		prbad("Error 02: Your SD card is write protected! If using a full size SD card, ensure that the lock switch is facing upwards.")
		prinfo("Visual aid: https://nintendohomebrew.com/assets/img/nhmemes/sdlock.png")
		exitOnEnter()
	else:
		prgood("SD card is writeable!")

consoleNames = {
	1: "Old 3DS/2DS, 11.8.0 to 11.17.0",
	2: "New 3DS/2DS, 11.8.0 to 11.17.0",
	3: "Old 3DS/2DS, 11.4.0 to 11.7.0",
	4: "New 3DS/2DS, 11.4.0 to 11.7.0"
}

primaryConsoleVersions = [ 1, 2 ]
secondaryConsoleVersions = [ 3, 4 ]

consoleIndex = 0

encodedID1s = {
	1: "01C08FE21CFF2FE111990B488546696507A10122044B984768465946C0AA171C4346024CA047B84771A0050899CE0408730064006D00630000900A0862003900",
	2: "01C08FE21CFF2FE111990B488546696507A10122044B984768465946C0AA171C4346024CA047B84771A005085DCE0408730064006D00630000900A0862003900",
	3: "01C08FE21CFF2FE111990B488546696507A10122044B984768465946C0AA171C4346024CA047B847499E050899CC0408730064006D00630000900A0862003900",
	4: "01C08FE21CFF2FE111990B488546696507A10122044B984768465946C0AA171C4346024CA047B847459E050881CC0408730064006D00630000900A0862003900"
}

ID0, ID0Count, ID1, ID1Count = "", 0, "", 0

class haxStates:
    ID1_NOT_PRESENT = 0
    NOT_READY = 1
    READY_TO_INJECT = 2
    TRIGGER_FILE_REMOVED = 3

haxStateLabel = {
	haxStates.ID1_NOT_PRESENT: "\033[30;1mID1 not created\033[0m",
	haxStates.NOT_READY: "\033[33;1mNot ready - check MSET9 status for more details\033[0m",
	haxStates.READY_TO_INJECT: "\033[32mReady\033[0m",
	# "\033[32;1mInjected\033[0m", # you must go
	haxStates.TRIGGER_FILE_REMOVED: "\033[32mRemoved trigger file\033[0m"
}

haxState = haxStates.ID1_NOT_PRESENT

realID1Path = ""
realID1BackupTag = "_user-id1"

hackedID1 = ""
hackedID1Path = ""

homeMenuExtdata = [0x8F,  0x98,  0x82,  0xA1,  0xA9,  0xB1]  # us,eu,jp,ch,kr,tw
miiMakerExtdata = [0x217, 0x227, 0x207, 0x267, 0x277, 0x287]  # us,eu,jp,ch,kr,tw
trigger = "002F003A.txt"  # all 3ds ":/" in hex format
triggerFilePath = ""

def pickConsoleVersion():
	clearScreen()
	print(f"MSET9 {VERSION} SETUP by zoogie, Aven, DannyAAM and thepikachugamer")
	print("What is your console model and version?")
	print("Old 3DS has two shoulder buttons (L and R)")
	print("New 3DS has four shoulder buttons (L, R, ZL, ZR)")

	print("\n-- Please type in a number then hit return --\n")

	print("Enter one of these numbers!")
	for i in primaryConsoleVersions:
		print(f"{i}: {consoleNames[i]}")

	print("9: Other firmware versions")

	selectedIndex = getInput([*primaryConsoleVersions, 9])
	if selectedIndex < 0:
		prgood("Goodbye!")
		exitOnEnter()

	if selectedIndex != 9:
		return selectedIndex

	for i in secondaryConsoleVersions:
		print(f"{i}: {consoleNames[i]}")

	print("0: Back")
	selectedIndex = getInput([*secondaryConsoleVersions, 0])
	if selectedIndex < 0:
		prgood("Goodbye!")
		exitOnEnter()

	if selectedIndex != 0:
		return selectedIndex

	return pickConsoleVersion()


def createHaxID1():
	global consoleIndex, ID0, hackedID1, hackedID1Path, realID1Path, realID1BackupTag

	selectedIndex = pickConsoleVersion()

	hackedID1 = bytes.fromhex(encodedID1s[selectedIndex]).decode("utf-16le")

	if consoleIndex == 0:
		print("\033[0;33m=== DISCLAIMER ===\033[0m") # 5;33m? The blinking is awesome but I also don't want to frighten users lol
		print()
		print("This process will temporarily reset all your 3DS data.")
		print("All your applications and themes will disappear.")
		print("This is perfectly normal, and if everything goes right, it will re-appear")
		print("at the end of the process.")
		print()
		print("In any case, it is highly recommended to make a backup of your SD card's contents to a folder on your PC.")
		print("(Especially the 'Nintendo 3DS' folder.)")
		print()

		print("Input '1' again to confirm.")
		print("Input '2' to cancel.")
		time.sleep(3)
		if getInput(range(1, 2)) != 1:
			print()
			prinfo("Cancelled.")
			return

		if not realID1Path.endswith(realID1BackupTag):
			prinfo("Backing up original ID1...")
			os.rename(abs(realID1Path), abs(realID1Path + realID1BackupTag))

		try:
			hackedID1Path = ID0 + "/" + hackedID1
			prinfo("Creating hacked ID1...")
			os.mkdir(abs(hackedID1Path))
			prinfo("Creating dummy databases...")
			os.mkdir(abs(hackedID1Path + "/dbs"))
			open(abs(hackedID1Path + "/dbs/title.db"), "w").close()
			open(abs(hackedID1Path + "/dbs/import.db"), "w").close()
		except Exception as exc:
			if isinstance(exc, OSError) and osver == "Windows" and exc.winerror == 234: # WinError 234 my love
				prbad("Error 18: Windows locale settings are broken!")
				prinfo("Consult https://3ds.hacks.guide/troubleshooting-mset9.html for instructions.")
				prinfo("If you need help, join Nintendo Homebrew on Discord: https://discord.gg/nintendohomebrew")
			elif isinstance(exc, OSError) and osver == "Linux" and exc.errno == 22: # Don't want this message to display on Windows if it ever manages to
				prbad("Failed to create hacked ID1!") # Give this an error number?
				prbad(f"Error details: {str(exc)}")
				prinfo("Please unmount your SD card and remount it with the 'utf8' option.") # Should we do this ourself? Like look at macOS
			else:
				prbad("An unknown error occured!")
				prbad(f"Error details: {str(exc)}")
				prinfo("Join Nintendo Homebrew on Discord for help: https://discord.gg/nintendohomebrew")

			exitOnEnter()

		prgood("Created hacked ID1.")
		return

	elif selectedIndex == consoleIndex:
		prinfo("No change made.")
		return

	else:
		os.rename(abs(hackedID1Path), abs(ID0 + "/" + hackedID1))
		hackedID1Path = ID0 + "/" + hackedID1
		prinfo(f"Switched to \"{consoleNames[selectedIndex]}\".")
		return

titleDatabasesGood = False
menuExtdataGood = False
miiExtdataGood = False
miiPlazaExtdata = False

def sanity():
	global hackedID1Path, titleDatabasesGood, menuExtdataGood, miiExtdataGood, miiPlazaExtdata

	# prinfo("Checking databases...")
	checkTitledb  = softcheck(hackedID1Path + "/dbs/title.db",  0x31E400, silent=True)
	checkImportdb = softcheck(hackedID1Path + "/dbs/import.db", 0x31E400, silent=True)
	titleDatabasesGood = not (checkTitledb or checkImportdb)
	if not titleDatabasesGood:
		if not os.path.exists(abs(hackedID1Path + "/dbs")):
			os.mkdir(abs(hackedID1Path + "/dbs"))
		# Stub them both. I'm not sure how the console acts if title.db is fine but not import. Someone had that happen, once
		open(abs(hackedID1Path + "/dbs/title.db"),  "w").close()
		open(abs(hackedID1Path + "/dbs/import.db"), "w").close()

	# prinfo("Checking for HOME Menu extdata...")
	for i in homeMenuExtdata:
		if os.path.exists(abs(hackedID1Path + f"/extdata/00000000/{i:08X}")):
			menuExtdataGood = True
			break

	# prinfo("Checking for Mii Maker extdata...")
	for i in miiMakerExtdata:
		if os.path.exists(abs(hackedID1Path + f"/extdata/00000000/{i+1:08X}")):
			miiPlazaExtdata = True

		if os.path.exists(abs(hackedID1Path + f"/extdata/00000000/{i:08X}")):
			miiExtdataGood = True
			break

	return menuExtdataGood and miiExtdataGood and titleDatabasesGood

def sanityReport():
	prinfo(f"Current dir: {scriptroot}")

	if not menuExtdataGood:
		prbad("HOME menu extdata: Missing!")
		prinfo("Please power on your console with your SD inserted, then check again.")
		prinfo("If this does not work, your SD card may need to be reformatted.")
	else:
		prgood("HOME menu extdata: OK!")

	print()

	if not miiExtdataGood:
		prbad("Mii Maker extdata: Missing!")
		prinfo("Please power on your console with your SD inserted, then launch Mii Maker.")
		# *
		if miiPlazaExtdata:
			prinfo("Reminder: Mii Maker is the app with the \"Mii\" icon; StreetPass Mii Plaza is different!")
	else:
		prgood("Mii Maker extdata: OK!")

	print()

	if not titleDatabasesGood:
		prbad("Title database: Not initialized!")
		prinfo("Please power on your console with your SD inserted, open System Setttings,")
		prinfo("navigate to Data Management -> Nintendo 3DS -> Software, then select Reset.")
	else:
		prgood("Title database: OK!")

	print()

def injection():
	global haxState, hackedID1Path, trigger

	triggerFilePath = hackedID1Path + "/extdata/" + trigger

	freeSpace = shutil.disk_usage(scriptroot).free
	if freeSpace < 16 * 1024 * 1024: # This is a good time to actually check the space
		prbad(f"Error 06: You need at least 16MB free space on your SD card, you have {(freeSpace / 1000000):.2f} bytes!")
		prinfo("Please free up some space and try again.")
		return

	prinfo("Injecting trigger file...")
	with open(abs(triggerFilePath), 'w') as f:
		f.write("pls be haxxed mister arm9, thx")
		f.close()

	prgood("MSET9 successfully injected!")

def remove():
	global ID0, ID1, hackedID1Path, realID1Path, realID1BackupTag, titleDatabasesGood

	prinfo("Removing MSET9...")

	if hackedID1Path and os.path.exists(abs(hackedID1Path)):
		if not os.path.exists(abs(realID1Path + "/dbs")) and titleDatabasesGood:
			prinfo("Moving databases to user ID1...")
			os.rename(abs(hackedID1Path + "/dbs"), abs(realID1Path + "/dbs"))

		prinfo("Deleting hacked ID1...")
		shutil.rmtree(abs(hackedID1Path))

	if os.path.exists(abs(realID1Path) and realID1Path.endswith(realID1BackupTag)):
		prinfo("Renaming original ID1...")
		os.rename(abs(realID1Path), abs(ID0 + "/" + ID1[:32]))
		ID1 = ID1[:32]
		realID1Path = ID0 + "/" + ID1

	haxState = haxStates.ID1_NOT_PRESENT
	prgood("Successfully removed MSET9!")

def softcheck(keyfile, expectedSize = None, crc32 = None, silent = False):
	filename = keyfile.rsplit("/")[-1]

	if not os.path.exists(abs(keyfile)):
		silent or prbad(f"{filename} does not exist on SD card!")
		return 1

	fileSize = os.path.getsize(abs(keyfile))
	if not fileSize:
		silent or prbad(f"{filename} is an empty file!")
		return 1
	elif expectedSize and fileSize != expectedSize:
		silent or prbad(f"{filename} is size {fileSize:,} bytes, not expected {expectedSize:,} bytes")
		return 1

	if crc32:
		with open(abs(keyfile), "rb") as f:
			checksum = binascii.crc32(f.read())
			f.close()
			if crc32 != checksum:
				silent or prbad(f"{filename} was not recognized as the correct file")
				return 1

	silent or prgood(f"{filename} looks good!")
	return 0

def is3DSID(name):
	if not len(name) == 32:
		return False

	try:
		hex_test = int(name, 0x10)
	except:
		return False

	return True


# Section: Sanity checks A (global files required for exploit)
writeProtectCheck()

prinfo("Ensuring extracted files exist...")

fileSanity = 0
fileSanity += softcheck("boot9strap/boot9strap.firm", crc32=0x08129C1F)
fileSanity += softcheck("boot.firm")
fileSanity += softcheck("boot.3dsx")
fileSanity += softcheck("b9", crc32=0xD59F0CAD)
fileSanity += softcheck("SafeB9S.bin")

if fileSanity > 0:
	prbad("Error 03: One or more files are missing or malformed!")
	prinfo("Please re-extract the MSET9 zip file, overwriting any existing files when prompted.")
	exitOnEnter()

# prgood("All files look good!")

# Section: sdwalk
for dirname in os.listdir(abs("Nintendo 3DS/")):
	fullpath = "Nintendo 3DS/" + dirname

	if not os.path.isdir(abs(fullpath)):
		prinfo(f"Found file in Nintendo 3DS folder? '{dirname}'")
		continue

	if not is3DSID(dirname):
		continue

	prinfo(f"Detected ID0: {dirname}")
	ID0 = fullpath
	ID0Count += 1

if ID0Count != 1:
	prbad(f"Error 04: You don't have 1 ID0 in your Nintendo 3DS folder, you have {ID0Count}!")
	if ID0Count == 0:
		prinfo("Do not manually create the \"Nintendo 3DS\" folder. Delete the folder for now: the guide will create it on its own.")
	else:
		prinfo("Consult: https://3ds.hacks.guide/troubleshooting-mset9.html for help!")
	exitOnEnter()

for dirname in os.listdir(abs(ID0)):
	if need_hangul_fix():
		dirname = fix_hangul(dirname)
	fullpath = ID0 + "/" + dirname

	if not os.path.isdir(abs(fullpath)):
		prinfo(f"Found file in ID0 folder? '{dirname}'")
		continue

	if is3DSID(dirname) or (dirname[32:] == realID1BackupTag and is3DSID(dirname[:32])):
		prinfo(f"Detected ID1: {dirname}")
		ID1 = dirname
		realID1Path = ID0 + "/" + ID1
		ID1Count += 1
	elif "sdmc" in dirname and len(dirname) == 32:
		currentHaxID1enc = dirname.encode("utf-16le").hex().upper()

		for haxID1index in encodedID1s:
			if currentHaxID1enc == encodedID1s[haxID1index]:
				consoleIndex = haxID1index
				break

		if consoleIndex == 0: # shouldn't happen
			prbad("Unrecognized hacked ID1 in ID0 folder, removing!")
			shutil.rmtree(abs(fullpath))

		prinfo(f"Detected hacked ID1 for {consoleNames[consoleIndex]}")
		hackedID1Path = fullpath
		triggerFilePath = abs(hackedID1Path + "/extdata/" + trigger)
		sanityOK = sanity()

		if os.path.exists(triggerFilePath):
			os.remove(triggerFilePath)
			haxState = haxStates.TRIGGER_FILE_REMOVED
		elif sanityOK:
			haxState = haxStates.READY_TO_INJECT
		else:
			haxState = haxStates.NOT_READY

if ID1Count != 1:
	prbad(f"Error 05: You don't have 1 ID1 in your Nintendo 3DS folder, you have {ID1Count}!")
	prinfo("Consult: https://3ds.hacks.guide/troubleshooting-mset9.html for help!")
	exitOnEnter()

if haxState != haxStates.ID1_NOT_PRESENT and not realID1Path.endswith(realID1BackupTag): # ?
	os.rename(abs(realID1Path), abs(realID1Path + realID1BackupTag))

clearScreen()
print(f"MSET9 {VERSION} SETUP by zoogie, Aven, DannyAAM and thepikachugamer")
print()
print(f"Current MSET9 state: {haxStateLabel[haxState]}")

print("\n-- Please type in a number then hit return --\n")

print("↓ Input one of these numbers!")

if haxState == haxStates.ID1_NOT_PRESENT:
	print("1. Create MSET9 ID1")
else:
	print(f"1. Change console version (Current: {consoleNames[consoleIndex]})")
	print("2. Check MSET9 status")
	print("3. Inject trigger file")
	print("4. Remove MSET9")

print("\n0. Exit")

while 1:
	try_chdir() # (?)

	optSelect = getInput(range(0, 5))
	if optSelect <= 0:
		break

	elif optSelect == 1: # Create hacked ID1
		createHaxID1()
		exitOnEnter()

	elif optSelect == 2: # Check status
		if haxState == haxStates.ID1_NOT_PRESENT:
			prbad("Can't do that now!")
			continue
		sanityReport()
		exitOnEnter()

	elif optSelect == 3: # Inject trigger file
		if haxState != haxStates.READY_TO_INJECT:
			prbad("Can't do that now!")
			continue
		injection()
		exitOnEnter()

	elif optSelect == 4: # Remove MSET9
		if haxState == haxStates.ID1_NOT_PRESENT:
			prinfo("Nothing to do.")
			continue

		remove()
		exitOnEnter()

prgood("See ya later, alligator...")
time.sleep(2)
