# CRCUtil
Portable CRC32 Checksum Tool – Generate & Compare

> [!NOTE]
> Installation is supported only for the following: 
> - Windows (amd64)
> - Linux (amd64)
>    - X11
>    - Wayland


## Table of Contents

* [Installation](#installation)
* [Usage](#usage)
  * [crc](#crc)
  * [diff](#diff)
  * [pause/resume](#pauseresume)
* [Development](#development)

## Installation
> [!NOTE]
> - Requires Python 3.11+<br >
### Windows & Linux (X11)
```bash
pip install crcutil
```

### Linux (Wayland)
> [!CAUTION]
> - This will add your user to the <i>input</i> group and immediately log you out.
> - This makes it possible in Wayland to track keyboard presses; necessary for the playback controls
```bash
pip install crcutil
sudo usermod -aG input $USER
sudo pkill -u $USER
```

## Usage

### crc

Generate CRC32 checksums
> [!NOTE]
> - This will output a crc.json file in the supplied -o argument.
> - If no -o supplied a crc.json is created in the current directory.
> - If a crc.json already exists in the current directory, a crc2.json is created.
```bash
crcutil crc -l 'C:\path_to_traverse' -o 'C:\path_to_output.json'
```
-----
### diff
Diff output can be generated from 2 separate crc files
> [!NOTE]
> - This will compare both crc files and output a diff.json in the supplied -o argument.<br >
> - If no -o supplied a diff.json is created in the current directory.

```bash
crcutil diff -l 'C:\crc_1.json' 'C:\crc_2.json' -o 'C:\diff.json'
```
---

### Pause/Resume 
> [!CAUTION]
> The crc can only be resumed as long as the contents/structure of the traversed location have not changed

> [!NOTE]
> To resume a crc after exiting, pass the location of the existing crc to the -o flag<br >
> i.e: ```crcutil crc -l 'C:\path_to_traverse' -o 'C:\existing_crc.json'```

- The tool can be paused/resumed at any time by pressing:
    - p
        - Windows
        - Linux (X11)
    - alt+p
        - Linux (Wayland)
- The tool can be exited at any time by pressing:
    - q
        - Windows
        - Linux (X11)
    - alt+q
        - Linux (Wayland)

## Development

> [!NOTE]
> Development requires a fully configured [Dotfiles](https://github.com/florez-carlos/dotfiles) dev environment <br>

```bash
source init.sh
```


