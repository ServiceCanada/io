#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );

use cPanelUserConfig;
use Storable qw/dclone/; 
use Path::Tiny qw/path/;

use Prism;
use DBI;
use YAML::Tiny;
use Text::CSV_XS;
use DateTime;


# =================
# = PREPROCESSING =
# =================
my $prism = Prism->new( file => 'index.yml' );

my $dbh = DBI->connect(
    "dbi:SQLite:dbname=".$prism->parent('public')->sibling(  $prism->config->{'database'}->{'path'} )
    ,"","", { sqlite_unicode => 1, AutoCommit => 0 }
);

my $add = $dbh->prepare( $prism->config->{'database'}->{'sql'}->{'create'} );
my $update = $dbh->prepare( $prism->config->{'database'}->{'sql'}->{'update'} );

my $rc = 1; 

while ( my $resource = $prism->next() )
{    
    my $io = $prism->download( $resource->{'uri'}, $resource->{'source'} );
    
    if ( $io == undef )
    {
        $io = $prism->basedir->child( $resource->{'source'} );
    }
        
    $io = $io->openr;
    
    my $csv = Text::CSV_XS->new ( { binary => 1 } )  # should set binary attribute.
                    or die "Cannot use CSV: ".Text::CSV->error_diag ();
                    
    $csv->column_names( @{ $csv->getline( $io ) } );
    
    while (my $row = $csv->getline_hr($io) )
    {
        my $rez = dclone( $resource );
        my $dataset = $prism->transform( $row, $rez );
        
        $dataset = normalize( $dataset );
        
        # lets check if this recall exists
        if ( my ( $id, $sub, $title, $lang, $year ) = $dbh->selectrow_array( 
                        $prism->config->{'database'}->{'sql'}->{'read'}, {},
                        $dataset->{'id'}, $dataset->{'lang'} )
        ){
          
            unless ( $sub =~ m/\b\Q$dataset->{'subcategory'}\E\b/ )
            {
                # We are merging here
                print " [merging] [$dataset->{lang}] ".$dataset->{'url'}."\n";
                
                $title .= ', ' . $dataset->{'subcategory'} unless $title =~ m/\b\Q$dataset->{'subcategory'}\E\b/;
                $sub .= ';' . $dataset->{'subcategory'};
                $year .= ';' . $dataset->{'year'} unless $year =~ m/\b\Q$dataset->{'year'}\E\b/;
                $update->execute( $title, $sub, $year , $id, $lang );
            }
            next;
        }
        
        $add->execute( map { $dataset->{$_} }  split ' ', $prism->config->{'database'}->{'sql'}->{'fields'} );
        print " [added] [$dataset->{lang}] ".$dataset->{'url'}."\n";
        
        unless ( $rc++ % 1000 )
        {
            print " [commit] adding record changes to DB\n";
            $dbh->commit;
        }
    }
    
    # commit any last changes
    $dbh->commit;
    
}

say "[complete] OK";

sub normalize
{
    my ( $dataset ) = @_ ;
    
    my $normalized = {};
    
    foreach my $entry ( keys $dataset )
    {
        $normalized->{ $entry } = ( $dataset->{ $entry } eq 'Not Entered' || $dataset->{ $entry } eq 'Non Saisie')
                                        ? '' : $dataset->{ $entry };
    }
    
    return $normalized;
}
