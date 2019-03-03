#!/usr/bin/perl
use common::sense;

use cPanelUserConfig;

use Env;
use File::Spec;
use lib File::Spec->catdir( substr( $DOCUMENT_ROOT, 0, rindex( $DOCUMENT_ROOT, '/')  ), 'cgi-lib');

use Mustache::Simple;
use Path::Tiny qw/path/;
use YAML::Tiny;

use CGI qw(-utf8);
use CGI::Carp qw( fatalsToBrowser );
use IO::Compress::Zip qw(zip $ZipError) ;
use XML::XML2JSON;

$CGI::POST_MAX = 1024 * 1024 * 5;       # max upload 1MB

my $PANDOC = path($DOCUMENT_ROOT)->sibling('vendor/pandoc/'.$^O.'/pandoc')->stringify;
my $XML2JSON = XML::XML2JSON->new( content_key => 'text');
# =================
# = PREPROCESSING =
# =================
my $config = YAML::Tiny->read( path($0)->sibling('index.yml')->stringify )->[0];
my $stache = Mustache::Simple->new();
my $q = CGI->new();
# ============
# = RESPONSE =
# ============
print $q->header("text/html;charset=UTF-8");

my $upload_folder = path($0)->sibling( $config->{'uploads'} );
my $packages = path($0)->sibling( $config->{'packages'} );

# lets clean the directories;
$_->remove_tree({ keep_root => 1, safe => 0 }) for ( $upload_folder, $packages );


my @files = $q->multi_param('input-files');
my @io_handles = $q->multi_param('input-files');

my $inventory = inventory( \@io_handles, $upload_folder );

my @zip = ();

foreach my $doc ( $inventory->children( qr/\.docx$/) )
{
    my $file = $doc->stringify();

    my $html = substr( $file, 0, -5).".html";
    my $pdf = substr( $file, 0, -5).".pdf";
    my $json = substr( $file, 0, -5).".json";
        
    system( $PANDOC, $file, '-s', '-o', $html);    
    system( $PANDOC, $file, '-s', '-o', $pdf);  
    
    my ( $body ) = normalize( $html )->slurp_raw =~ /<body>(.*?)<\/body>/gsi;
   
    path( $json )->spew_raw(
        $XML2JSON->convert( '<document>'.$body.'</document>' )
    );
    
    # add to the zip file;
    push @zip, path($_)->basename for ( $file, $html, $json, $pdf );
}

my $ziparchive = $packages->child(  $inventory->basename().'.zip' )->absolute->touchpath;

compress( $inventory, $ziparchive, \@zip );

print $stache->render( path($0)->sibling('complete.html')->absolute->slurp_utf8, { link => "/".$ziparchive->relative( $DOCUMENT_ROOT )->stringify, title => 'Archive to download'} );

# ====================
# = HELPER FUNCTIONS =
# ====================

sub inventory
{
    my ( $ios, $basedir ) = @_;
      
    # Now lets store the files
    $basedir = $basedir->child( time );
    
    $basedir->mkpath({mode => 0755});
    
    foreach my $io ( @{ $ios } )
    {
        my $base = path($io)->basename();
        my $temp = path( $q->tmpFileName( $io ) );
        my $dest = $basedir->child( $base )->touchpath;
        
        $temp->copy( $dest->stringify );
    }
    return $basedir->absolute;
}

sub normalize
{
    my $file = path( shift );
    
    my $html = $file->slurp_raw;
    
    $html =~ s/<li><p>/<li>/g;
    $html =~ s/<\/p><\/li>/<\/li>/g;
    $html =~ s/’/'/g;
    
    $file->spew_raw( $html );
    
    return $file;
    
}

sub compress
{
   my ( $inventory, $archive, $files ) = @_;

   my $current = Path::Tiny->cwd;
    
   chdir $inventory->stringify;

   zip $files => $archive->stringify or die "zip failed: $ZipError\n";
    
   chdir $current;

}
