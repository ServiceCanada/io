#!/usr/bin/perl
use common::sense;

use cPanelUserConfig;

use Env;
use File::Spec;
use lib File::Spec->catdir( substr( $DOCUMENT_ROOT, 0, rindex( $DOCUMENT_ROOT, '/')  ), 'cgi-lib');

use Mustache::Simple;
use Path::Tiny qw/path/;
use YAML::Tiny;

use CGI;
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
print $q->header; 

my $upload_folder = path($0)->sibling( $config->{'uploads'} );
my $packages = path($0)->sibling( $config->{'packages'} );

# lets clean the directories;
$_->remove_tree({ keep_root => 1, safe => 0 }) for ( $upload_folder, $packages );


my @files = $q->param('input-files');
my @io_handles = $q->upload('input-files');

my $inventory = inventory( \@io_handles, $upload_folder );

my @zip = ();

foreach my $doc ( $inventory->children( qr/\.docx$/) )
{
    my $file = $doc->stringify();

    my $html = substr( $file, 0, -5).".html";
    my $json = substr( $file, 0, -5).".json";
	    
    system( $PANDOC, $file, '-o', $html);    
    
    normalize( $html );
    
    path( $json )->spew_utf8(
        $XML2JSON->convert( '<document>'.path( $html )->slurp_utf8.'</document>' )
    );
    
    # add to the zip file;
    push @zip, path($_)->basename for ( $file, $html, $json ); 
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
    
    my $html = $file->slurp_utf8;
    
    $html =~ s/<li><p>/<li>/g;
    $html =~ s/<\/p><\/li>/<\/li>/g;
    $html =~ s/’/'/g;
    
    $file->spew_utf8( $html );
    
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
