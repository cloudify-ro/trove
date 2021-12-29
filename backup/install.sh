#!/usr/bin/env bash
set -e

export APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1
APTOPTS="-y -qq --no-install-recommends --allow-unauthenticated"

function install_mariadb() {
    apt-key adv --fetch-keys 'https://mariadb.org/mariadb_release_signing_key.asc'
    add-apt-repository "deb [arch=amd64] https://mirror1.hs-esslingen.de/pub/Mirrors/mariadb/repo/$1/ubuntu $(lsb_release -cs) main"
    apt-get install $APTOPTS mariadb-backup
}

function install_postgres() {
    apt-key adv --fetch-keys 'https://www.postgresql.org/media/keys/ACCC4CF8.asc'
    add-apt-repository "deb [arch=amd64] http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main"
    apt-get install $APTOPTS postgresql-client-$1
}

function instal_percona_xtrabackup() {
    curl -sSL https://repo.percona.com/apt/percona-release_latest.$(lsb_release -sc)_all.deb -o percona-release.deb
    dpkg -i percona-release.deb
    percona-release enable-only tools release
    apt-get update
    apt-get install $APTOPTS percona-xtrabackup-$2
    rm -f percona-release.deb
}

case "$1" in
"mysql")
    case "$2" in
    "5.7")
      instal_percona_xtrabackup "24"
    ;;
    "8.0")
      instal_percona_xtrabackup "80"
    ;;
    esac
;;
"mariadb")
    install_mariadb $2
    ;;
"postgresql")
    install_postgres $2
    ;;
*)
    echo "datastore $1 not supported"
    exit 1
    ;;
esac

apt-get clean
rm -rf /var/lib/apt/lists/*
