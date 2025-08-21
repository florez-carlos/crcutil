# CRCUtil
A CLI tool that recursively traverses a given location and generates a
crc.json containing a CRC checksum value for every encountered file/dir

> [!NOTE]
> Installation is supported only for the following: 
> - Windows
> - Linux

> [!NOTE]
> Development requires a fully configured 
[Dotfiles](https://github.com/florez-carlos/dotfiles)
dev environment <br>

## Table of Contents

* [Installation](#installation)
  * [pip](#pip)
* [Usage](#usage)
  * [crc](#crc)
  * [diff](#diff)
  * [pause/resume](#pauseresume)
* [Development](#development)

## Installation
### Pip
```bash
python3 -m pip install crcutil
```

## Usage

### crc

-l The location for which to generate the crc

```bash
crcutil crc -l 'C:\path_to_traverse' -o 'C:\path_to_output.json'
```
This will output a crc.json file in the supplied -o argument or
if no -o argument supplied, then to the default output location: <br >
- Windows
```bash
C:\Users\<USERNAME>\Documents\crcutil\
```
- Linux
```bash
$HOME/crcutil
```
### Diff
If you hold 2 crc files generated from the same directory
and would like to compare the differences.

-l The location of both crc files to compare

```bash
crcutil diff -l 'C:\crc_1.json' 'C:\crc_2.json' -o 'C:\diff.json'
```

This will compare both crc files and generate a diff.json in the supplied -o argument or
if no -o argument supplied, then to the default output location: <br >
- Windows
```bash
C:\Users\<USERNAME>\Documents\crcutil\
```
- Linux
```bash
$HOME/crcutil
```
### Pause/Resume 
- The program can be paused/resumed at any time by pressing p.
- If you exit the program or it crashes unexpectedly mid operation, 
invoke the same command and the program will continue where it left off,
as long as the crc file is not corrupted

## Development

> [!NOTE]
> Development requires a fully configured [Dotfiles](https://github.com/florez-carlos/dotfiles) dev environment <br>

```bash
source init.sh
```


