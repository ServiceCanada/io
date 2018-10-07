#!/usr/bin/env perl
use common::sense;

use Env;
use File::Spec;
use lib File::Spec->catdir( substr( $DOCUMENT_ROOT, 0, rindex( $DOCUMENT_ROOT, '/')  ), 'cgi-lib');

use cPanelUserConfig;
use Path::Tiny qw/path/;

use YAML::Tiny;
use JSON::MaybeXS;
use CGI::Compress::Gzip;


# =================
# = PREPROCESSING =
# =================
my $config = YAML::Tiny->read( path($0)->sibling('index.yml')->stringify )->[0];

# ============
# = RESPONSE =
# ============
my $cgi = CGI::Compress::Gzip->new();