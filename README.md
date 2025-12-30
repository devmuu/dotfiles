[![License](https://img.shields.io/badge/License-GPL--3.0-green)](LICENSE_GPL-3.0.md)

# Dot Files

Personal dotfiles.
Use stow tool to create sym links.

# Examples

To make file links only.

```{bash}
stow --no-folding --restow FOLDER_NAME
```

To delete links:

```{bash}
stow -D FOLDER_NAME
```
