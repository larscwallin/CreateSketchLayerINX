#!/usr/bin/env python

""" 
Version 0.1 110205

This script was written by Lars Wallin to make bitmap sketching easy. 

It simply,

1. takes the currently selected element (a white/transparent surface seems a logical choice), 
2. exports it to png
3. inserts it as a linked image element into a new layer in the current Inkscape drawing
4. opens the png in your editor of choice
5. lets you sketch away on the bitmap
6. waits for the sketching app to close
7. updates the linked bitmap in Inkscape

After this i use the bitmap to auto, or, manualy trace .

Have fun :)

PS. 
  Written on Ubuntu. If you run Windows make sure that you change the save path for the bitmap
  as it defaults the Linux:y /home/
                                    DS.

"""

import inkex

import sys, os, commands,subprocess
import string
import png

import time
from xml.dom.minidom import Document
from xml.dom.minidom import DocumentType

# This line is only needed if you don't put the script directly into
# the installation directory

# sys.path.append('/usr/share/inkscape/extensions')

# The simplestyle module provides functions for style parsing.
from simplestyle import *
        
# Effect main class
class CreateSketchLayer(inkex.Effect):

    parserProcessHandle = None
    saveLocation = ""
    where = ""
    what = ""
    sketch_name = ""
    remove_border = ""
    replace_source = ""
    sketch_editor = ""
    svg_file = ""
    renderHistory = []
    rectangle_id = "" 

    def __init__(self):
        """
        Constructor.
        Defines the "--what" option of a script.
        """

        # Call the base class constructor.
        inkex.Effect.__init__(self)

        # The OptionParser stuff below are Inkscape specific code which sets up the dialog for the extension GUI.
        # The current options are just lab stuff and should be substituted with something more usefull. 
        
        # Define string option "--what" with "-w" shortcut.
        self.OptionParser.add_option('-w', '--what', action = 'store',
              type = 'string', dest = 'what', default = '',
              help = '')
          
        self.OptionParser.add_option('--where', action = 'store',
              type = 'string', dest = 'where', default = '',
              help = 'Where to save?')
    
        self.OptionParser.add_option('--sketch_name', action = 'store',
              type = 'string', dest = 'sketch_name', default = 'New Sketch',
              help = 'Sketch name')
    
        self.OptionParser.add_option('--remove_border', action = 'store',
              type = 'string', dest = 'remove_border', default = '',
              help = 'Remove canvas border?')

        self.OptionParser.add_option('--replace_source', action = 'store',
              type = 'string', dest = 'replace_source', default = '',
              help = 'Replace source element with sketch input?')
    
        self.OptionParser.add_option('--sketch_editor', action = 'store',
              type = 'string', dest = 'sketch_editor', default = 'gimp',
              help = 'Application name for sketching. This value will be used at the command line, so please use the key used for starting the app in this context.')

    
        
    
	# exportImage takes as argument the current svg element id. This is then used to select which element the Inkscape exe should export.
    def exportImage(self,id):
            
        # The easiest way to name rendered elements is by using their id since we can trust that this is always unique.
        filename = os.path.join(self.where, id+'.png')

        #self.debugPrint(filename)

        # Inkscape has many really useful cmd line arguments which can be used to query for data, and render bitmaps.
        # Please not that Inkscape supports shell execution and should really be started as such at the beginning of parsing. 
        # The shell spawning stuff is commented out at the bottom of this script.
        # The current command will start/close a new instance of the app for every element parsed.     

        command = 'inkscape --without-gui --export-id-only --export-id %s --export-png %s %s' % (id, filename, self.svg_file)
        
        #self.debugPrint(command)
        
        processHandle = subprocess.Popen(command,
                   shell=True,
                   stdout=subprocess.PIPE)

        # Inkscape is gracious enough to return some metadata regarding the exported bitmap.
        stdout_value = processHandle.communicate()[0]

        # Inkscapes element metadata is not a pleasant format. parseImageMetaData data tries to remedy this.            

        return (filename)


    def openImage(self,filename,sketch_editor):
        
        #self.debugPrint(filename)

        command = '%s "%s"' % (sketch_editor,filename)
        
        processHandle = subprocess.Popen(command,
                   shell=True,
                   stdout=subprocess.PIPE)

        stdout_value = processHandle.communicate()[0]
    
    
    def effect(self):
    
        """
        Effect behaviour.
        Overrides base class method
        """

        self.svg_file = self.args[-1]

        # Get script's "--what" option value.
        self.what = self.options.what

        # Get script's "--where" option value.
        self.where = self.options.where

        self.debugPrint(self.replace_source)

        if(self.where==''): sys.exit()

        self.sketch_name = self.options.sketch_name
        self.sketch_editor = self.options.sketch_editor
        self.sketch_editor = self.sketch_editor  if self.sketch_editor != '' else ''
        
        sketch_file_path = ''
        sketch_canvas = ''
        sketch_canvas_x = ''
        sketch_canvas_y = ''
        sketch_canvas_height = ''
        sketch_canvas_width = ''
        sketch_canvas_id = ''        
        
        svg = self.document.xpath('//svg:svg',namespaces=inkex.NSS)[0]
        
        layer_width  = self.unittouu(svg.get('width'))
        layer_height  = self.unittouu(svg.get('height'))
        
        # Create layer element
        layer = inkex.etree.SubElement(svg, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), '%s' % (self.sketch_name))              
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        

        self.getselected()
        
        if(self.selected.__len__() > 0):
          
          sketch_canvas = self.selected.values()
          sketch_canvas = sketch_canvas[0]
                    
          if(sketch_canvas!=''):

            sketch_bitmap_path = self.createBitmapFile(sketch_canvas)
            
            if(sketch_bitmap_path != ''):
              # Create and insert a new image element for the sketch bitmap
              sketch_bitmap_element = inkex.etree.SubElement(layer,'image')

              # Set rectangle position to top/left width/height.
              sketch_bitmap_element.set('x', str(sketch_canvas_x))
              sketch_bitmap_element.set('y', str(sketch_canvas_y))
              sketch_bitmap_element.set('width', str(sketch_canvas_width))
              sketch_bitmap_element.set('height', str(sketch_canvas_height))
              
              # Set basic style attributes 
              sketch_bitmap_element.set(inkex.addNS('href', 'xlink'), str(sketch_bitmap_path))
              
              # Connect elements together.                
              layer.append(sketch_bitmap_element)		
              
              try:
                self.openImage(sketch_bitmap_path,self.sketch_editor)
              except:                
                self.debugPrint('Editor error')	

              if(self.replace_source != ""):
                sketch_canvas.getparent().remove(sketch_canvas)
        else:
          
          # As we have no selected canvas element we create a <rect> with the same dimensions as the layer
          canvas = self.createCanvasElement(layer_width, layer_height, 0, 0, layer)

          # And the we create a bitmap representation to paint on
          sketch_bitmap_path = self.createBitmapFile(canvas, useInkscape=False)

          if(sketch_bitmap_path != ''):
            # Create and insert a new image element for the sketch bitmap
            sketch_bitmap_element = inkex.etree.SubElement(layer,'image')

            # Set rectangle position to top/left width/height.
            sketch_bitmap_element.set('x', str(0))
            sketch_bitmap_element.set('y', str(0))
            sketch_bitmap_element.set('width', str(layer_width))
            sketch_bitmap_element.set('height', str(layer_height))
            
            # Set basic style attributes 
            sketch_bitmap_element.set(inkex.addNS('href', 'xlink'), str(sketch_bitmap_path))
            
            # Connect elements together.                
            layer.append(sketch_bitmap_element)   
            
            try:
              self.openImage(sketch_bitmap_path,self.sketch_editor)
            except:                
              self.debugPrint('Editor error') 

            if(self.replace_source != ""):
              sketch_canvas.getparent().remove(sketch_canvas)
          

          else:

            pass


    def createCanvasElement(self, w, h ,x, y, layer):
      
      now = (time.strftime("%I%M%S"))

      # Create canvas element

      canvas = inkex.etree.SubElement(layer, 'rect')
      canvas.set(inkex.addNS('label', 'inkscape'), '%s' % (self.sketch_name))              
      canvas.set(inkex.addNS('groupmode', 'inkscape'), 'layer')      
      canvas.set('id', '%s-%s' % (self.sketch_name, now))  

      canvas.set('x', str(x))
      canvas.set('y', str(y))
      canvas.set('width', str(w))
      canvas.set('height', str(h))
      canvas.set('style', 'fill:#ffffff;fill-opacity:0')      

      return canvas


    def createBitmapFile(self, sketch_canvas, useInkscape=True):

      # Get the position of the sketch element
      sketch_canvas_id = sketch_canvas.get('id')
      sketch_canvas_x = sketch_canvas.get('x')
      sketch_canvas_y = sketch_canvas.get('y')
      sketch_canvas_height = sketch_canvas.get('height')
      sketch_canvas_width = sketch_canvas.get('width')
      
      # Export the selected element as sketch bitmap
      if(useInkscape):
        sketch_bitmap_path = self.exportImage(sketch_canvas_id)
      else:

        sketch_bitmap_path = os.path.join(self.where, sketch_canvas_id+'.png')
        sketch_canvas_width = int(round(float(sketch_canvas_width)))
        sketch_canvas_height = int(round(float(sketch_canvas_height)))

        # Create the png pixel arrays. Each pixel has two values: 1 black and white value, and one alpha. 
        # In the case below it will result in a [0,0] pixel which is a black transparent pixel.
        rows = [[0 for element in xrange(2) for number_of_pixles in xrange(sketch_canvas_width)] for number_of_rows in xrange(sketch_canvas_height)]

        png.from_array(rows, 'LA').save(sketch_bitmap_path)



      return sketch_bitmap_path

    def debugPrint(self,textStr):
        debugLayer = self.document.xpath('//svg:svg/svg:g',namespaces=inkex.NSS)[0]
        
        # Create text element
        text = inkex.etree.Element(inkex.addNS('text','svg'))
        text.text = str(textStr)

        # Set text position to center of document.
        text.set('x', str(300 / 2))
        text.set('y', str(300 / 2))

        # Center text horizontally with CSS style.
        style = {'text-align' : 'center', 'text-anchor': 'middle'}
        text.set('style', formatStyle(style))

        # Connect elements together.
        debugLayer.append(text)


# Create effect instance and apply it.
effect = CreateSketchLayer()
effect.affect()


