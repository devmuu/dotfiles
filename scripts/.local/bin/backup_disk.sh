#!/bin/bash

# device name and label
get_device_by_label() {
    LABEL="$1"

    DEVICE=$(lsblk -fpP | grep "LABEL=\"${LABEL}\"" | awk -F'[= ]+' '{print $2}' | tr -d '"')
    echo "${DEVICE}"
}

# echo device
get_device_path() {
    LABEL="$1"
    DEVICE=$(get_device_by_label "${LABEL}")

    if [ -z "${DEVICE}" ]; then
        echo "Device ${LABEL} not found!"
        exit 1
    fi

    echo "${DEVICE}"
}

# unlock lucks device
unlock_luks() {
    DEVICE="$1"
    LABEL="storage-01"

    sleep 2
    echo "Open LUKS device ${DEVICE}..."
    sudo cryptsetup luksOpen "${DEVICE}" "${LABEL}"

    sleep 2
    echo "Initializing mount process ..."

    udisksctl mount -b /dev/mapper/"${LABEL}"
    echo "Device ${LABEL} mounted."
}

# disconnect luks device
lock_luks() {
    DEVICE="$1"
    LABEL="$2"

    sleep 2
    echo "Disconnecting LUKS ${LABEL}..."
    udisksctl unmount -b /dev/mapper/"${LABEL}"

    sleep 2
    echo "Closing LUKS..."
    sudo cryptsetup luksClose "${LABEL}"

    sleep 2
    echo "Poweroff device..."
    udisksctl power-off -b "${DEVICE}"

    sleep 2
    echo "Device can be disconnected."
}

# unmount not encrypted device
unmount_device() {
    DEVICE="$1"

    sleep 2
    echo "Disconnecting ${DEVICE} ..."
    udisksctl unmount -b "${DEVICE}"

    sleep 2
    echo "Poweroff device..."
    udisksctl power-off -b "${DEVICE}"

    sleep 2
    echo "Device can be disconnected."
}

# rsync backup
perform_backup() {
    MOUNT_POINT="$1"
    PREFIX="$2"
    LABEL="$3"

    RSYNC_ARGS="-avh --inplace --no-whole-file --delete-before --info=progress2"

    echo "Init backup..."

    sleep 1

    rsync ${RSYNC_ARGS} \
        /home/storage/misc/media/audio/ ${MOUNT_POINT}/${PREFIX}misc/media/audio

    if [[ ${LABEL} != "storage-04" ]]; then
        rsync ${RSYNC_ARGS} \
            /home/storage/root/ ${MOUNT_POINT}/${PREFIX}root

        rsync ${RSYNC_ARGS} \
            /home/storage/tmp/ ${MOUNT_POINT}/${PREFIX}tmp

        rsync ${RSYNC_ARGS} \
            /home/storage/user/ ${MOUNT_POINT}/${PREFIX}user \
            --exclude shadercache \
            --exclude "Proton *" \
            --exclude "SteamLinux*" \
            --exclude "Steamworks Shared" \
            --exclude "steamapps/downloading" \
            --exclude "steamapps/shadercache" \
            --exclude "steamapps/temp"

        rsync ${RSYNC_ARGS} \
            /home/storage/work/ ${MOUNT_POINT}/${PREFIX}work
    fi

    echo "Backup finish."
}

# get distro info
DISTRO=$(source /etc/os-release; echo $NAME | awk '{print tolower($1)}')

# set mount path based on distro
case ${DISTRO} in
    debian)
        MOUNT_PATH="/media/${USER}"
    ;;
    fedora|arch)
        MOUNT_PATH="/run/media/${USER}"
    ;;
esac

# params
case "$1" in
    "unlock") unlock_luks "storage-01" ;;
    "lock") lock_luks "storage-01" ;;
    "restore") perform_backup "$folder_in" "$folder_out" ;;
    *)
        LABEL=$1
        if [[ "${LABEL}" == storage-* ]]; then
            echo "Init backup to $1..."

            DEVICE=$(get_device_path "${LABEL}")
            MOUNT_POINT="$MOUNT_PATH/${LABEL}"
            FS_TYPE=$(lsblk -fpP | grep "LABEL=\"${LABEL}\"" | awk -F'[= ]+' '{print $4}' | tr -d '"')

            # if not mounted, assume luks
            if ! mount | grep -q "${MOUNT_POINT}"; then
                 echo "Not mounted. LUKS device."
                 DEVICE=$(lsblk -fpP | grep "FSTYPE=\"crypto_LUKS\"" | awk -F'[= ]+' '{print $2}' | tr -d '"')
                 unlock_luks "${DEVICE}"
            fi

            echo "DEVICE: ${DEVICE}"
            echo "MOUNT IN: ${MOUNT_POINT}"
            echo "FS: ${FS_TYPE}"

            if [[ "${FS_TYPE}" == "btrfs" ]]; then
                PREFIX="@"
            else
                PREFIX=
            fi

            perform_backup "${MOUNT_POINT}" "${PREFIX}" "${LABEL}"

            # disconnect and power off device
            if [[ ${LABEL} == "storage-01" ]]; then
                lock_luks "${DEVICE}" "${LABEL}"
            else
                unmount_device "${DEVICE}"
            fi

        else
            echo "No device."
        fi
    ;;
esac

