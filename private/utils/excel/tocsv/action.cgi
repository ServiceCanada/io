#!/usr/bin/env perl
use common::sense;

use Env;
use File::Spec;
use lib File::Spec->catdir( substr( $DOCUMENT_ROOT, 0, rindex( $DOCUMENT_ROOT, '/')  ), 'cgi-lib');

use cPanelUserConfig;
use Path::Tiny qw/path/;

use YAML::Tiny;
use Text::CSV_XS;
use Mustache::Simple;

use CGI qw(-utf8);
use Spreadsheet::ParseXLSX;

# =================
# = PREPROCESSING =
# =================

my $dir = path($0)->realpath;
my $base = path( substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/private/' ) ) );

# lets ensure we do not have any files stagnant
houseclean( $dir->sibling('conversions') );

my $cgi = CGI->new();

print $cgi->header("text/html;charset=UTF-8");

my $config = YAML::Tiny->read( $dir->sibling('index.yml')->stringify )->[0];
my $stache = Mustache::Simple->new();
my $parser = Spreadsheet::ParseXLSX->new;

my ( $xls, $name ) = (
     path( $cgi->tmpFileName( $cgi->param('input-file') ) ),
     path( $cgi->param('input-file') )->basename( '.xlsx' )
 );


my $io = $dir->sibling('conversions')->child( $name.".csv" );
my $fio = $io->openw_utf8;

my $csv = Text::CSV_XS->new ( { binary => 1 } )  # should set binary attribute.
                or die "Cannot use CSV: ".Text::CSV->error_diag ();

my $excel = $parser->parse( $xls->absolute->stringify );
my ( $sheet ) = ( $excel->worksheets() );

my ( $row_min, $row_max ) = $sheet->row_range();
my ( $col_min, $col_max ) = $sheet->col_range();

 for my $row ( $row_min .. $row_max ) {
 	my @line = ();
    for my $col ( $col_min .. $col_max )
    {
    	my $cell = $sheet->get_cell( $row, $col );
    	my $value = ( $cell ) ? $cell->value() : "";
    	push( @line, sanitize( $value ) );
    }
    $csv->say( $fio, \@line );
 }

 print $stache->render( $dir->sibling('complete.html')->absolute->slurp_utf8, { link => "/".$io->relative( $DOCUMENT_ROOT )->stringify, title => $name.".csv"  } );

 
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
