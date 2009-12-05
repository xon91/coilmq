"""
A collection of STOMP frame convenience classes.

These classes are built around the C{stomper.Frame} class, primarily making it more 
convenient to construct frame instances.
"""
__authors__ = ['"Hans Lellelid" <hans@xmpl.org>']
__copyright__ = "Copyright 2009 Hans Lellelid"
__license__ = """Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
 
  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License."""
import stomper

class StompFrame(stomper.Frame):
    """ Convenience subclass of C{stomper.Frame} which provides a simpler
    construction API and automatically adds the content-length header, when applicable.
    
    """
    
    def __init__(self, cmd=None, headers=None, body=None):
        """
        Initialize new StompFrame with command, headers, and body.
        """
        if body is None:
            body = '' # Making it compatible w/ superclass
        if headers is None:
            headers = {}
        if cmd: # Only set if not None, since cmd prop setter will validate command is valid 
            self.cmd = cmd
        self.body = body
        self.headers = headers
    
    def __getattr__(self, name):
        """ Convenience way to return header values as if they're object attributes. 
        
        We replace '-' chars with '_' to make the headers python-friendly.  For example:
        
        frame.headers['message-id'] == frame.message_id
        """
        return self.headers.get(name.replace('-', '_'))
    
    def __repr__(self):
        return '<%s cmd=%s>' % (self.__class__.__name__, self.cmd)
    
class HeaderValue(object):
    """
    An class that can serve as a placeholder and return a calculated value using a
    passed-in calculator function when it is cast to string.
    
    This function implements the __str__ method to return the calculated value.  That gets 
    the desired value into the packed STOMP message.  While according to 
    U{http://docs.codehaus.org/display/STOMP/Character+Encoding} there seems to some general
    idea about having UTF-8 as the character encoding for headers; however the C{stomper} lib
    does not support this currently.
    
    For example, to use this class to generate the content-length header:
    
    >>> frame = StompFrame(cmd='MESSAGE', body='12345')
    >>> frame.headers['content-length'] = HeaderValue(calculator=lambda: len(frame.body))
    >>> frame.pack()
    CONNECT\n12345
    """
    def __init__(self, calc):
        """
        @param calc: The calculator callable that will yield the desired value.
        @type calc: C{callable}
        """
        if not callable(calc):
            raise ValueError("Non-callable param: %s" % calc)
        self.calc = calc
    
    def __str__(self):
        """ Returns the result of the calculator function (cast to C{str}). """
        return str(self.calc())
    
    def __repr__(self):
        return '<%s calc=%s>' % (self.__class__.__name__, self.calc)

# ---------------------------------------------------------------------------------
# Server Frames
# ---------------------------------------------------------------------------------

class ConnectedFrame(StompFrame):
    """ A CONNECTED server frame (response to CONNECT).
    
    @ivar session: The (throw-away) session ID to include in response.
    @type session: C{str} 
    """
    def __init__(self, session):
        """
        @param session: The (throw-away) session ID to include in response.
        @type session: C{str}
        """
        StompFrame.__init__(self, 'CONNECTED', headers={'session': session})

class MessageFrame(StompFrame):
    """ A MESSAGE server frame. """
    
    def __init__(self, body=None):
        """
        @param body: The message body bytes.
        @type body: C{str} 
        """
        StompFrame.__init__(self, 'MESSAGE', body=body)
        self.headers['content-length'] = HeaderValue(calc=lambda: len(self.body))
        
# TODO: Figure out what we need from ErrorFrame (exception wrapping?)
class ErrorFrame(StompFrame):
    """ An ERROR server frame. """
    
    def __init__(self, message, body=None):
        """
        @param body: The message body bytes.
        @type body: C{str} 
        """
        StompFrame.__init__(self, 'ERROR', body=body)
        self.headers['message'] = message
        self.headers['content-length'] = HeaderValue(calc=lambda: len(self.body))
    
    def __repr__(self):
        return '<%s message=%r>' % (self.__class__.__name__, self.headers['message']) 
    
class ReceiptFrame(StompFrame):
    """ A RECEIPT server frame. """
    
    def __init__(self, receipt):
        """
        @param receipt: The receipt message ID.
        @type receipt: C{str}
        """
        StompFrame.__init__(self, 'RECEIPT', headers={'receipt': receipt})