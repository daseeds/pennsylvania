CKEDITOR.plugins.add( 'customparagraph',
{
    init: function( editor )
    {
        editor.addCommand('addParagraphClassName',{
            exec : function( editor ){    
                var ps = editor.document.$.getElementsByTagName("p");
                for (var i=0; i < ps.length; i++){

                    if(ps[i].className.indexOf("lead") < 0){
                        ps[i].className += "lead";
                    }

                }

            }
        });

        editor.ui.addButton( 'ThinyP',{
            label: 'Appends lead class',
            command: 'addParagraphClassName',
            icon: this.path + 'images/icon.png'
        });
    }
} );