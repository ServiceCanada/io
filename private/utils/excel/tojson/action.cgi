#!/usr/bin/env perl

use strict;
use warnings;
use utf8;
use feature ':5.12';
use CGI qw(-utf8);

use Env;

use File::Spec;
#use lib File::Spec->catdir( substr( $DOCUMENT_ROOT, 0, rindex( $DOCUMENT_ROOT, '/')  ), 'cgi-lib');
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/private/' ) ), 'cgi-lib' );

use cPanelUserConfig;
use Path::Tiny qw/path/;

use YAML::Tiny;
use JSON::XS;
use Spreadsheet::ParseXLSX;
use Mustache::Simple;

use Time::Piece;
use Archive::Zip;
use Try::Tiny;
use Text::Slugify 'slugify';


# =================
# = PREPROCESSING =
# =================

my ( $base, $conversion, $coder, $stache ) = (
        path($0)->parent,
        path($0)->sibling('conversions'),
        JSON::XS->new->pretty->utf8,
        Mustache::Simple->new()
);

# lets ensure we do not have any files stagnant
houseclean( $conversion );

my $cgi = CGI->new();

print $cgi->header("text/html;charset=UTF-8");

my $parser = Spreadsheet::ParseXLSX->new;

my $dir = $conversion->child( localtime->epoch );

# lets make the path;
$dir->mkpath();

my $workbook = $parser->parse( path( $cgi->tmpFileName( $cgi->param('input-file') ) )->absolute->stringify );

#my $workbook = $parser->parse( path('test.xlsx' )->absolute->stringify );
for my $worksheet ( $workbook->worksheets() ) {
    
    my ( $row_min, $row_max ) = $worksheet->row_range();
    my $name = $worksheet->get_name();
    
    my $dataset = [];
    
    for my $row ( 1 .. $row_max ) {
        
        my $check = $worksheet->get_cell( $row, 0 );
        next unless ( $check && $check->value() ne '' );
        
        try {
            push( @{ $dataset }, {
               task => { en => $worksheet->get_cell( $row, 1 )->value(), fr =>  $worksheet->get_cell( $row, 3 )->value() },
               institution => { en => $worksheet->get_cell( $row, 5 )->value() , fr => $worksheet->get_cell( $row, 7 )->value() }
            });
        }
    }
    
    $dir->child( slugify($name).'.json' )->spew_raw( $coder->encode( $dataset ) );
}

my $zip = Archive::Zip->new();

$zip->addTree( $dir->absolute->realpath->stringify );

$zip->overwriteAs( { filename => $conversion->child( $dir->basename.'.zip')->absolute->realpath->stringify } );

$dir->remove_tree({safe => 0});

print $stache->render( path($0)->sibling('complete.html')->absolute->slurp_utf8, { link => "/".$conversion->child( $dir->basename.'.zip')->relative( $DOCUMENT_ROOT )->stringify, title => $dir->basename.'.zip'  } );

 
# ============================ ->
#  Functions
#  =========================== ->

sub houseclean
{
	my ( $dir ) = @_;

	foreach	my $file ( grep { $_->is_file() } $dir->children )
	{
		if ( ( time - $file->stat->ctime ) > 60*3 ) 
		{
			$file->remove();
		};	
	}

	return $dir;
}

sub sanitize
{
	my ( $text ) = @_;
	$text =~ s/^\s+|\s+$//g;
	$text =~ s/_x000[D0]_//g;
	return $text;
}
