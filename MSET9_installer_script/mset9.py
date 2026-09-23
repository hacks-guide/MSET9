#!/usr/bin/python3
import abc, sys, os, platform, shutil, time, pathlib, binascii

VERSION = "v2.1"

class state:
    ID1_NOT_PRESENT = 0
    NOT_READY = 1
    READY_TO_INJECT = 2
    INJECTED = 3
    TRIGGER_FILE_REMOVED = 4

def prgood(content):
	# print(f"[\033[0;32m✓\033[0m] {content}")
	# so that people aren't confused by the [?]. stupid Windows.
	print(f"[\033[0;32mOK\033[0m] {content}")

def prbad(content):
	print(f"[\033[0;91mXX\033[0m] {content}")

def prinfo(content):
	print(f"[--] {content}")

def exitOnEnter(errCode = 0):
	input("[--] Press Enter to exit...")
	exit(errCode)

osver = platform.system()
thisfile = os.path.abspath(__file__)
scriptroot = os.path.dirname(thisfile)
systmp = None

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
	except Exception:
		prbad("Error 08: Couldn't reapply working directory, is SD card reinserted?")
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
	prbad("Error 01: Couldn't find Nintendo 3DS folder! Ensure that you are running this script from the root of the SD card.")
	prbad("If that doesn't work, eject the SD card, and put it back in your console. Turn it on and off again, then rerun this script.")
	prinfo(f"Current dir: {scriptroot}")
	exitOnEnter()

# Section: sdWritable
def writeProtectCheck():
	global fs
	prinfo("Checking if SD card is writeable...")
	if not is_writable():
		prbad("Error 02: Your SD card is write protected! If using a full size SD card, ensure that the lock switch is facing upwards.")
		prinfo("Visual aid: https://nintendohomebrew.com/assets/img/nhmemes/sdlock.png")
		exitOnEnter()
	else:
		prgood("SD card is writeable!")

# Section: SD card free space
# ensure 16MB free space
freeSpace = shutil.disk_usage(scriptroot).free
if not freeSpace >= 16 * 1024 * 1024:
	prbad(f"Error 06: You need at least 16MB free space on your SD card, you have {(freeSpace / 1000000):.2f} bytes!")
	prbad("Error 06: You need at least 16MB free space on your SD card!")
	prinfo("Please free up some space and try again.")
	exitOnEnter()

clearScreen()
print(f"MSET9 {VERSION} SETUP by zoogie, Aven, DannyAAM and thepikachugamer")
print("What is your console model and version?")
print("Old 3DS has two shoulder buttons (L and R)")
print("New 3DS has four shoulder buttons (L, R, ZL, ZR)")

print("\n-- Please type in a number then hit return --\n")

consoleNames = {
	1: "Old 3DS/2DS, 11.8.0 to 11.17.0",
	2: "New 3DS/2DS, 11.8.0 to 11.17.0",
	3: "Old 3DS/2DS, 11.4.0 to 11.7.0",
	4: "New 3DS/2DS, 11.4.0 to 11.7.0"
}

print("Enter one of these four numbers!")
for i in consoleNames:
	print(f"Enter {i} for: {consoleNames[i]}")

# print("Enter 1 for: Old 3DS/2DS, 11.8.0 to 11.17.0")
# print("Enter 2 for: New 3DS/2DS, 11.8.0 to 11.17.0")
# print("Enter 3 for: Old 3DS/2DS, 11.4.0 to 11.7.0")
# print("Enter 4 for: New 3DS/2DS, 11.4.0 to 11.7.0")

encodedID1s = {
	1: "01C08FE21CFF2FE111990B488546696507A10122044B984768465946C0AA171C4346024CA047B84771A0050899CE0408730064006D00630000900A0862003900",
	2: "01C08FE21CFF2FE111990B488546696507A10122044B984768465946C0AA171C4346024CA047B84771A005085DCE0408730064006D00630000900A0862003900",
	3: "01C08FE21CFF2FE111990B488546696507A10122044B984768465946C0AA171C4346024CA047B847499E050899CC0408730064006D00630000900A0862003900",
	4: "01C08FE21CFF2FE111990B488546696507A10122044B984768465946C0AA171C4346024CA047B847459E050881CC0408730064006D00630000900A0862003900"
}

consoleIndex = getInput(range(1, 4))
if consoleIndex < 0:
	prgood("Goodbye!")
	exitOnEnter()

ID0, ID0Count, ID1, ID1Count = "", 0, "", 0

haxStates = ["\033[30;1mID1 not created\033[0m", "\033[33;1mNot ready - check MSET9 status for more details\033[0m", "\033[32mReady\033[0m", "\033[32;1mInjected\033[0m", "\033[32mRemoved trigger file\033[0m"]
haxState = state.ID1_NOT_PRESENT

realID1Path = ""
realID1BackupTag = "_user-id1"

hackedID1 = bytes.fromhex(encodedID1s[consoleIndex]).decode("utf-16le")  # ID1 - arm injected payload in readable format
hackedID1Path = ""

homeMenuExtdata = [0x8F,  0x98,  0x82,  0xA1,  0xA9,  0xB1]  # us,eu,jp,ch,kr,tw
miiMakerExtdata = [0x217, 0x227, 0x207, 0x267, 0x277, 0x287]  # us,eu,jp,ch,kr,tw
trigger = "002F003A.txt"  # all 3ds ":/" in hex format
triggerFilePath = ""

def createHaxID1():
	global fs, ID0, hackedID1Path, realID1Path, realID1BackupTag

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

	if osver == "Linux": # ...
		print("(on Linux, things like to not go right - please ensure that your SD card is mounted with the 'utf8' option.)")
		print()

	print("Input '1' again to confirm.")
	print("Input '2' to cancel.")
	time.sleep(3)
	if getInput(range(1, 2)) != 1:
		print()
		prinfo("Cancelled.")
		exitOnEnter()

	hackedID1Path = ID0 + "/" + hackedID1

	try:
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

	if not realID1Path.endswith(realID1BackupTag):
		prinfo("Backing up original ID1...")
		os.rename(abs(realID1Path), abs(realID1Path + realID1BackupTag))

	prgood("Created hacked ID1.")
	exitOnEnter()

titleDatabasesGood = False
menuExtdataGood = False
miiExtdataGood = False

def sanity():
	global fs, hackedID1Path, titleDatabasesGood, menuExtdataGood, miiExtdataGood

	prinfo("Checking databases...")
	checkTitledb  = softcheck(hackedID1Path + "/dbs/title.db",  0x31E400)
	checkImportdb = softcheck(hackedID1Path + "/dbs/import.db", 0x31E400)
	titleDatabasesGood = not (checkTitledb or checkImportdb)
	if not titleDatabasesGood:
		if not os.path.exists(abs(hackedID1Path + "/dbs")):
			os.mkdir(abs(hackedID1Path + "/dbs"))
		# Stub them both. I'm not sure how the console acts if title.db is fine but not import. Someone had that happen, once
		open(abs(hackedID1Path + "/dbs/title.db"),  "w").close()
		open(abs(hackedID1Path + "/dbs/import.db"), "w").close()

	prinfo("Checking for HOME Menu extdata...")
	for i in homeMenuExtdata:
		extdataRegionCheck = hackedID1Path + f"/extdata/00000000/{i:08X}"
		if os.path.exists(abs(extdataRegionCheck)):
			menuExtdataGood = True
			break
	
	prinfo("Checking for Mii Maker extdata...")
	for i in miiMakerExtdata:
		extdataRegionCheck = hackedID1Path + f"/extdata/00000000/{i:08X}"
		if os.path.exists(abs(extdataRegionCheck)):
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

def injection(create=True):
	global fs, haxState, hackedID1Path, trigger

	triggerFilePath = hackedID1Path + "/extdata/" + trigger

	if not os.path.exists(abs(triggerFilePath)) ^ create:
		prbad(f"Trigger file already {'injected' if create else 'removed'}!")
		return

	if os.path.exists(abs(triggerFilePath)):
		os.remove(abs(triggerFilePath))
		haxState = state.TRIGGER_FILE_REMOVED
		prgood("Removed trigger file.")
		return

	prinfo("Injecting trigger file...")
	with open(abs(triggerFilePath), 'w') as f:
		f.write("pls be haxxed mister arm9, thx")
		f.close()

	prgood("MSET9 successfully injected!")
	exitOnEnter()

def remove():
	global fs, ID0, ID1, hackedID1Path, realID1Path, realID1BackupTag, titleDatabasesGood

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

	haxState = 0
	prgood("Successfully removed MSET9!")

def softcheck(keyfile, expectedSize = None, crc32 = None):
	global fs
	filename = keyfile.rsplit("/")[-1]

	if not os.path.exists(abs(keyfile)):
		prbad(f"{filename} does not exist on SD card!")
		return 1

	fileSize = os.path.getsize(abs(keyfile))
	if not fileSize:
		prbad(f"{filename} is an empty file!")
		return 1
	elif expectedSize and fileSize != expectedSize:
		prbad(f"{filename} is size {fileSize:,} bytes, not expected {expectedSize:,} bytes")
		return 1

	if crc32:
		with open(abs(keyfile), "rb") as f:
			checksum = binascii.crc32(f.read())
			f.close()
			if crc32 != checksum:
				prbad(f"{filename} was not recognized as the correct file")
				return 1

	prgood(f"{filename} looks good!")
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
fileSanity += softcheck("b9")
fileSanity += softcheck("SafeB9S.bin")

if fileSanity > 0:
	prbad("Error 07: One or more files are missing or malformed!")
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
		currentHaxID1index = 0

		for haxID1index in encodedID1s:
			if currentHaxID1enc == encodedID1s[haxID1index]:
				currentHaxID1index = haxID1index
				break

		if currentHaxID1index == 0 or (hackedID1Path and os.path.exists(abs(hackedID1Path))): # shouldn't happen
			prbad("Unrecognized/duplicate hacked ID1 in ID0 folder, removing!")
			shutil.rmtree(abs(fullpath))
		elif currentHaxID1index != consoleIndex:
			prbad("Error 03: Don't change console model/version in the middle of MSET9!")
			print(f"Earlier, you selected: '[{currentHaxID1index}.] {consoleNames[currentHaxID1index]}'")
			print(f"Now, you selected:	 '[{consoleIndex}.] {consoleNames[consoleIndex]}'")
			print()
			print("Please re-enter the number for your console model and version.")

			choice = getInput([consoleIndex, currentHaxID1index])
			if choice < 0:
				prinfo("Cancelled.")
				hackedID1Path = fullpath
				remove()
				exitOnEnter()

			elif choice == currentHaxID1index:
				consoleIndex = currentHaxID1index
				hackedID1 = dirname

			elif choice == consoleIndex:
				os.rename(abs(fullpath), abs(ID0 + "/" + hackedID1))

		hackedID1Path = ID0 + "/" + hackedID1
		sanityOK = sanity()

		if os.path.exists(abs(hackedID1Path + "/extdata/" + trigger)):
			triggerFilePath = hackedID1Path + "/extdata/" + trigger
			haxState = state.INJECTED # Injected.
		elif sanityOK:
			haxState = state.READY_TO_INJECT # Ready!
		else:
			haxState = state.NOT_READY # Not ready...

if ID1Count != 1:
	prbad(f"Error 05: You don't have 1 ID1 in your Nintendo 3DS folder, you have {ID1Count}!")
	prinfo("Consult: https://3ds.hacks.guide/troubleshooting-mset9.html for help!")
	exitOnEnter()

def mainMenu():
	clearScreen()
	print(f"MSET9 {VERSION} SETUP by zoogie, Aven, DannyAAM and thepikachugamer")
	print(f"Using {consoleNames[consoleIndex]}")
	print()
	print(f"Current MSET9 state: {haxStates[haxState]}")

	print("\n-- Please type in a number then hit return --\n")

	print("↓ Input one of these numbers!")

	print("1. Create MSET9 ID1")
	print("2. Check MSET9 status")
	print("3. Inject trigger file")
	print("4. Remove trigger file")

	if haxState != 3:
		print("5. Remove MSET9")

	print("\n0. Exit")

	while 1:
		optSelect = getInput(range(0, 5))

		try_chdir() # (?)

		if optSelect <= 0:
			break

		elif optSelect == 1: # Create hacked ID1
			if haxState > state.ID1_NOT_PRESENT:
				prinfo("Hacked ID1 already exists.")
				continue
			createHaxID1()
			exitOnEnter()

		elif optSelect == 2: # Check status
			if haxState == state.ID1_NOT_PRESENT: # MSET9 ID1 not present
				prbad("Can't do that now!")
				continue
			sanityReport()
			exitOnEnter()

		elif optSelect == 3: # Inject trigger file
			if haxState != state.READY_TO_INJECT: # Ready to inject
				prbad("Can't do that now!")
				continue
			injection(create=True)
			# exitOnEnter() # has it's own

		elif optSelect == 4: # Remove trigger file
			if haxState < state.READY_TO_INJECT:
				prbad("Can't do that now!")
			injection(create=False)
			time.sleep(3)
			return mainMenu()

		elif optSelect == 5: # Remove MSET9
			if haxState <= state.ID1_NOT_PRESENT:
				prinfo("Nothing to do.")
				continue
			if haxState == state.INJECTED:
				prbad("Can't do that now!")
				continue

			remove()
			exitOnEnter()

mainMenu()
prgood("Goodbye!")
time.sleep(2)
