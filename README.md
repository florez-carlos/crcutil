# CRCUtil
Recursively traverses a given location and generates a hash.json containing a CRC value for every encountered file/dir

> [!NOTE]
> Installation is supported only for the following: 
> - Windows
> - Linux

> [!NOTE]
> Development requires a fully configured [Dotfiles](https://github.com/florez-carlos/dotfiles) dev environment <br>

## Table of Contents

* [Installation](#installation)
  * [pip](#pip)
* [Usage](#usage)
  * [hash](#hash)
  * [diff](#diff)
  * [pause/resume](#pauseresume)
* [Development](#development)

## Installation
### Pip
```bash
python3 -m pip install crcutil
```

## Usage

### Hash

-l The location for which to generate the hash

```bash
crcutil hash -l C:\DESIRED\PATH
```
This will generate a hash.json file in: <br >
- Windows
```bash
C:\Users\<USERNAME>\Documents\crcutil\
```
- Linux
```bash
$HOME/crcutil
```
### Diff
If you hold 2 hashes generated from the same directory and would like to compare the differences.

-l The location of both hash files to compare

```bash
crcutil diff -l C:\HASH_FILE_1.json C:\HASH_FILE_2.json
```

This will compare both hash files and generate a diff.json in:
- Windows
```bash
C:\Users\<USERNAME>\Documents\crcutil\
```
- Linux
```bash
$HOME/crcutil
```
### Pause/Resume 
- The program can be paused/resumed at any time by pressing p, if a CRC is being calculated for a file
you have to wait for the calculation to complete before the program can pause.
- If you exit the program or it crashes unexpectedly mid operation, invoke the same command and the program will continue where it left off,
as long as the hash file is not corrupted

## Development

> [!NOTE]
> Development requires a fully configured [Dotfiles](https://github.com/florez-carlos/dotfiles) dev environment <br>

```bash
source init.sh
```


