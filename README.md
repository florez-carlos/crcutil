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
* [Usage](#usage)
  * [crc](#crc)
  * [diff](#diff)
  * [pause/resume](#pauseresume)
* [Development](#development)

## Installation
> [!NOTE]
> - Requires Python 3.12+<br >
> - Requires pip

- Windows
```bash
pip install crcutil
```
- Linux
```bash
python3 -m pip install crcutil
```

## Usage

### crc

```bash
crcutil crc -l 'C:\path_to_traverse' -o 'C:\path_to_output.json'
```
> [!NOTE]
> This will output a crc.json file in the supplied -o argument.<br >
> If no -o argument is supplied, then the default output location is: <br >
- Windows
```bash
C:\Users\<USERNAME>\Documents\crcutil\
```
- Linux
```bash
$HOME/crcutil
```
### diff
If you hold 2 crc files generated from the same directory
and would like to compare the differences.

```bash
crcutil diff -l 'C:\crc_1.json' 'C:\crc_2.json' -o 'C:\diff.json'
```
> [!NOTE]
> This will compare both crc files and output a diff.json in the supplied -o argument.<br >
> If no -o argument is supplied, then the default output location is: <br >
- Windows
```bash
C:\Users\<USERNAME>\Documents\crcutil\
```
- Linux
```bash
$HOME/crcutil
```
### Pause/Resume 
- The tool can be paused/resumed at any time by pressing p.
- The tool can be exited at any time by pressing q (will continue where left off if you invoke the same command).

## Development

> [!NOTE]
> Development requires a fully configured [Dotfiles](https://github.com/florez-carlos/dotfiles) dev environment <br>

```bash
source init.sh
```


