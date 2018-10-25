#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );

use cPanelUserConfig;
use Path::Tiny qw/path/;
use Prism;
use DBI;
use YAML::Tiny;
use Text::CSV_XS;
use Storable qw/dclone/; 

# =================
# = PREPROCESSING =
# =================
my $prism = Prism->new( file => 'index.yml' );

my $dbh = DBI->connect(
    "dbi:SQLite:dbname=".$prism->parent('public')->sibling(  $prism->config->{'database'}->{'path'} )
    ,"","", { sqlite_unicode => 1 }
);

my $add = $dbh->prepare('INSERT INTO recalls ( id, title, abstract, date, lang, parent, category, subcategory, url ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)');


