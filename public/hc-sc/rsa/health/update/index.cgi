#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );

use cPanelUserConfig;
use Path::Tiny qw/path/;
use Prism;
use DBI;
use JSON;
use Storable qw/dclone/; 
use Data::Dumper;

use Digest::SHA qw(sha256_hex);

# =================
# = PREPROCESSING =
# =================
my $prism = Prism->new( file => 'index.yml' );

my $dbh = DBI->connect(
    "dbi:SQLite:dbname=".$prism->parent('public')->sibling(  $prism->config->{'database'}->{'path'} )
    ,"","", { sqlite_unicode => 1 }
);

my $coder = JSON->new->utf8;

my $add = $dbh->prepare( $prism->config->{'database'}->{'sql'}->{'create'} );

while (my $resource = $prism->next() )
{
    my $io = $coder->decode( $prism->get( $resource->{'uri'} )->{'content'} );
    
    foreach my $recall (  @{ $io->{'results'} }  )
    {
        my $predata = $prism->overlay( $recall, dclone( $resource ) );
                
        my ( $url, $uid ) = map { $predata->{ $_ } } ( 'source', 'id') ;
   
        next if ( my ( $id ) = $dbh->selectrow_array( $prism->config->{'database'}->{'sql'}->{'read'}, {}, $uid ) );
                
        my $data = $coder->decode( $prism->get( $url )->{'content'} );
        
        # lets set the category and sub category
        my $section = $data->{'panels'}->[0]->{'text'};

        $data->{'abstract'} = $data->{'panels'}->[1]->{'text'};

        my @secs = ( $section =~ m/<b>(Catégorie|Category):<\/b>(.*?)<BR\/>/ );

        $data->{ 'category' } = normalize( pop @secs );

        my $rez = dclone( $resource );

        my $dataset = $prism->transform( $data, $rez );
        
        $add->execute( map { $dataset->{$_} }  split ' ', $prism->config->{'database'}->{'sql'}->{'fields'} );
        print " [added] [$dataset->{lang}] ".$dataset->{'url'}."\n";
    
    }

}


sub normalize
{
    my ( $text ) = @_;

    $text =~ s/^\s+//;
    $text =~ s/\s+$//;

    return $text;
}
      
