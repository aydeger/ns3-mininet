""" Network topology
  Mininet 
    node 1 
  +---------+                                      +-------+
  | name    |                                      |  EPC  |
  | space 1 |                                      +-------+
  | ------- |                                          |
  | shell   |                                          |
  | ------- |                         +---------+      |
  | Linux   |                         |eNB      |------+ 
  | network |                         |Base     |                       | Mininet|   
  | stack   |                         |Station  |                       | node 2 |
  | ------- |                         +---------+                       +--------+
  | TAP     |                             |  |                          | TAP    | 
  | intf.   |                             |  |                          | intf.  |  
  +---------+      ns-3         ns-3      |  |     ns-3         ns-3    +--------+
       |           n0            n1       |  |      n1           n0         |
       |       +--------+    +--------+   |  |   +-------+    +-------+     |
       +-------|  tap   |    |        |   |  |   |       |    | tap   |-----+
               | bridge |    |        |   |  |   |       |    | bridge|
               +--------+    +----+---+   |  |   +--+----+    +-------+
               |  CSMA  |----|CSMA|UE | --+  +---|UE|CSMA|----| CSMA  |
               +--------+    +----+---+          +--+----+    +-------+
                   
               |<-------------------------------------------------->|
                                     ns-3 process
                                 in the root namespace

"""

import threading, time

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import OVSController

from mininet.log import info, error, warn, debug, setLogLevel
from mininet.node import Switch, Node
from mininet.link import Intf, Link
from mininet.util import quietRun, moveIntf, errRun

import ns.core
import ns.network
import ns.tap_bridge
import ns.csma
import ns.wifi
import ns.mobility
import ns.lte

# Default duration of ns-3 simulation thread. You can freely modify this value.

default_duration = 3600

# Set ns-3 simulator type to realtime simulator implementation.
# You can find more information about realtime modes here:
# http://www.nsnam.org/docs/release/3.17/manual/singlehtml/index.html#realtime
# http://www.nsnam.org/wiki/index.php/Emulation_and_Realtime_Scheduler

ns.core.GlobalValue.Bind( "SimulatorImplementationType", ns.core.StringValue( "ns3::RealtimeSimulatorImpl" ) )

# Enable checksum computation in ns-3 devices. By default ns-3 does not compute checksums - it is not needed
# when it runs in simulation mode. However, when it runs in emulation mode and exchanges packets with the real
# world, bit errors may occur in the real world, so we need to enable checksum computation.

ns.core.GlobalValue.Bind( "ChecksumEnabled", ns.core.BooleanValue ( "true" ) )

# Arrays which track all created TBIntf objects and Mininet nodes which has assigned an underlying ns-3 node.

allTBIntfs = []
allNodes = []

# These four global functions below are used to control ns-3 simulator thread. They are global, because
# ns-3 has one global singleton simulator object.

def start():
    """ Start the simulator thread in background.
        It should be called after configuration of all ns-3 objects
        (TBintfs, Segments and Links).
        Attempt of adding an ns-3 object when simulator thread is
        running may result in segfault. You should stop it first."""
    global thread
    if 'thread' in globals() and thread.isAlive():
        warn( "NS-3 simulator thread already running." )
        return
    # Install all TapBridge ns-3 devices not installed yet.
    for intf in allTBIntfs:
        if not intf.nsInstalled:
            intf.nsInstall()
    # Set up the simulator thread.
    thread = threading.Thread( target = runthread )
    thread.daemon = True
    # Start the simulator thread (this is where fork happens).
    # FORK!
    thread.start()
    # FORK:PARENT
    # Code below is executed in the parent thread.
    # Move all tap interfaces not moved yet to the right namespace.
    for intf in allTBIntfs:
        if not intf.inRightNamespace:
            intf.namespaceMove()
    return

def runthread():
    """ Method called in the simulator thread on its start.
        Should not be called manually."""
    # FORK:CHILD
    # Code below is executed in the simulator thread after the fork.
    # Stop event must be scheduled before simulator start. Not scheduling it
    # may lead leads to segfault.
    ns.core.Simulator.Stop( ns.core.Seconds( default_duration ) )
    # Start simulator. Function below blocks the Python thread and returns when simulator stops.
    ns.core.Simulator.Run()

def stop():
    """ Stop the simulator thread now."""
    # Schedule a stop event.
    ns.core.Simulator.Stop( ns.core.MilliSeconds( 1 ) )
    # Wait until the simulator thread stops.
    while thread.isAlive():
        time.sleep( 0.01 )
    return

def clear():
    """ Clear ns-3 simulator.
        It should be called when simulator is stopped."""
    ns.core.Simulator.Destroy()
    for intf in allTBIntfs:
        intf.nsInstalled = False
        intf.delete()
    for node in allNodes:
        del node.nsNode
    del allTBIntfs[:]
    del allNodes[:]
    return

# Functions for manipulating nodes positions. Nodes positioning is useful in
# wireless channel simulations: distance between nodes affects received signal power
# and, thus, throughput.
# Node positions are stored in the underlying ns-3 node (not in Mininet node itself).

def getPosition( node ):
    """ Return the ns-3 (x, y, z) position of a Mininet node.
        Coordinates are in the 3D Cartesian system.
        The unit is meters.
        node: Mininet node"""
    # Check if this Mininet node has assigned the underlying ns-3 node.
    if hasattr( node, 'nsNode' ) and node.nsNode is not None:
        # If it is assigned, go ahead.
        pass
    else:
        # If not, create new ns-3 node and assign it to this Mininet node.
        node.nsNode = ns.network.Node()
        allNodes.append( node )
    try:
        # Get postion coordinates from the ns-3 node
        mm = node.nsNode.GetObject( ns.mobility.MobilityModel.GetTypeId() )
        pos = mm.GetPosition()
        return ( pos.x, pos.y, pos.z )
    except AttributeError:
        warn( "ns-3 mobility model not found\n" )
        return ( 0, 0, 0 )

def setPosition( node, x, y, z ):
    """ Set the ns-3 (x, y, z) position of a Mininet node.
        Coordinates are in the 3D Cartesian system.
        The unit is meters.
        node: Mininet node
        x: integer or float x coordinate
        y: integer or float y coordinate
        z: integer or float z coordinate"""
    # Check if this Mininet node has assigned the underlying ns-3 node.
    if hasattr( node, 'nsNode' ) and node.nsNode is not None:
        # If it is assigned, go ahead.
        pass
    else:
        # If not, create new ns-3 node and assign it to this Mininet node.
        node.nsNode = ns.network.Node()
        allNodes.append( node )
    try:
        mm = node.nsNode.GetObject( ns.mobility.MobilityModel.GetTypeId() )
        if z is None:
            z = 0.0
        # Set postion coordinates in the ns-3 node
        pos = mm.SetPosition( ns.core.Vector( x, y, z ) )
    except AttributeError:
        warn( "ns-3 mobility model not found, not setting position\n" )

# TBIntf is the main workhorse of the module. TBIntf is a tap Linux interface located on Mininet
# node, which is bridged with ns-3 device located on ns-3 node.

class TBIntf( Intf ):
    """ Interface object that is bridged with ns-3 emulated device.
        This is a subclass of Mininet basic Inft object. """

    def __init__( self, name, node, port=None,
                  nsNode=None, nsDevice=None, mode=None, **params ):
        """name: interface name (e.g. h1-eth0)
           node: owning Mininet node (where this intf most likely lives)
           link: parent link if we're part of a link #TODO
           nsNode: underlying ns-3 node
           nsDevice: ns-3 device which the tap interface is bridged with
           mode: mode of TapBridge ns-3 device (UseLocal or UseBridge)
           other arguments are passed to config()"""
        self.name = name
        # Create a tap interface in the system, ns-3 TapBridge will connect to that interface later.
        self.createTap()
        # Set this Intf to be delayed move. This tells Mininet not to move the interface to the right
        # namespace during Intf.__init__(). Therefore, the interface must be moved manually later.
        # Actually, interfaces are moved right after the simulator thread start, in the start() global
        # function.
        self.delayedMove = True
        # If this node is running in its own namespace...
        if node.inNamespace:
            # ...this interface is not yet in the right namespace (it is in the root namespace just after
            # creation) and should be moved later.
            self.inRightNamespace = False
        else:
            # ...interface should stay in the root namespace, so it is in right namespace now.
            self.inRightNamespace = True
        # Initialize parent Intf object.
        Intf.__init__( self, name, node, port , **params)
        allTBIntfs.append( self )
        self.nsNode = nsNode
        self.nsDevice = nsDevice
        self.mode = mode
        self.params = params
        self.nsInstalled = False
        # Create TapBridge ns-3 device.
        self.tapbridge = ns.tap_bridge.TapBridge()
        # If ns-3 node and bridged ns-3 device are set and TapBridge mode is known...
        if self.nsNode and self.nsDevice and ( self.mode or self.node ):
            # ...call nsInstall().
            self.nsInstall()

    def createTap( self ):
        """Create tap Linux interface in the root namespace."""
        quietRun( 'ip tuntap add ' + self.name + ' mode tap' )

    def nsInstall( self ):
        """Install TapBridge ns-3 device in the ns-3 simulator."""
        if not isinstance( self.nsNode, ns.network.Node ):
            warn( "Cannot install TBIntf to ns-3 Node: "
                  "nsNode not specified\n" )
            return
        if not isinstance( self.nsDevice, ns.network.NetDevice ):
            warn( "Cannot install TBIntf to ns-3 Node: "
                  "nsDevice not specified\n" )
            return
        # If TapBridge mode has not been set explicitly, determine it automatically basing on
        # a Mininet node type. You can find more about TapBridge modes there:
        # http://www.nsnam.org/docs/release/3.18/models/singlehtml/index.html#tap-netdevice
        if self.mode is None and self.node is not None:
            # If Mininet node is some kind of Switch...
            if isinstance( self.node, Switch ):
                # ...use "UseBridge" mode. In this mode there may be many different L2 devices with
                # many source addresses on the Linux side of TapBridge, but bridged ns-3 device must
                # support SendFrom().
                self.mode = "UseBridge"
            else:
                # ...in the other case use "UseLocal" mode. In this mode there may be only one L2 source device
                # on the Linux side of TapBridge (TapBridge will change source MAC address of all packets coming
                # from the tap interface to the discovered address of this interface). In this mode bridged ns-3
                # device does not have to support SendFrom() (it uses Send() function to send packets).
                self.mode = "UseLocal"
        if self.mode is None:
            warn( "Cannot install TBIntf to ns-3 Node: "
                  "cannot determine mode: neither mode nor (mininet) node specified\n" )
            return
        # Set all required TapBridge attributes.
        self.tapbridge.SetAttribute ( "Mode", ns.core.StringValue( self.mode ) )
        self.tapbridge.SetAttribute ( "DeviceName", ns.core.StringValue( self.name ) )
        # Add TapBridge device to the ns-3 node.
        self.nsNode.AddDevice( self.tapbridge )
        # Set this TapBridge to be bridged with the specified ns-3 device.
        self.tapbridge.SetBridgedNetDevice( self.nsDevice )
        # Installation is done.
        self.nsInstalled = True

    def namespaceMove( self ):
        """Move tap Linux interface to the right namespace."""
        loops = 0
        # Wait until ns-3 process connects to the tap Linux interface. ns-3 process resides in the root
        # network namespace, so it must manage to connect to the interface before it is moved to the node
        # namespace. After interface move ns-3 process will not see the interface.
        while not self.isConnected():
            time.sleep( 0.01 )
            loops += 1
            if loops > 10:
                warn( "Cannot move TBIntf to mininet Node namespace: "
                      "ns-3 has not connected yet to the TAP interface\n" )
                return
        # Wait a little more, just for be sure ns-3 process not miss that.
        time.sleep( 0.01 )
        # Move interface to the right namespace.
        moveIntf( self.name, self.node )
        self.inRightNamespace = True
        # IP address has been reset while moving to namespace, needs to be set again.
        if self.ip is not None:
            self.setIP( self.ip, self.prefixLen )
        # The same for 'up'.
        self.isUp( True )

    def isConnected( self ):
        """Check if ns-3 TapBridge has connected to the Linux tap interface."""
        return self.tapbridge.IsLinkUp()

    def cmd( self, *args, **kwargs ):
        "Run a command in our owning node namespace or in the root namespace when not yet inRightNamespace."
        if self.inRightNamespace:
            return self.node.cmd( *args, **kwargs )
        else:
            cmd = ' '.join( [ str( c ) for c in args ] )
            return errRun( cmd )[ 0 ]

    def rename( self, newname ):
        "Rename interface"
        # If TapBridge is installed in ns-3, but ns-3 has not connected to the Linux tap interface yet...
        if self.nsInstalled and not self.isConnected():
            # ...change device name in TapBridge to the new one.
            self.tapbridge.SetAttribute ( "DeviceName", ns.core.StringValue( newname ) )
        Intf.rename( self, newname )

    def delete( self ):
        "Delete interface"
        if self.nsInstalled:
            warn( "You can not delete once installed ns-3 device, "
                  "run mininet.ns3.clear() to delete all ns-3 devices\n" )
        else:
            Intf.delete( self )



def UeNode(node, networkAddress, netMask, port=None, intfName=None, mode=None):
         #def __init__ (self, networkAddress=None, netMask=None, port=None, intfName=None, mode=None, DataRate=None, Delay=None ):
        """ create ue node
            node: mininet node
            networkAddress: IP network address, must be the same network as the node
            netMask: IP network mask
            port: node port number (optional)
            intfName: interface name (optional)
            DataRate: forced data rate of connected devices (optional), for example: 10Mbps, default: no-limit
        #       Delay: channel trasmission delay (optional), for example: 10ns, default: 0            
        """

        #    if DataRate is not None:
        #      self.csma.SetChannelAttribute( "DataRate", ns.network.DataRateValue( ns.network.DataRate( DataRate ) ) )
        #    if Delay is not None:
        #     self.csma.SetChannelAttribute( "Delay", ns.core.TimeValue( ns.core.Time( Delay ) ) )

        #def AddUe(self, node, networkAddress, netMask, port=None, intfName=None, mode=None):
        csma = ns.csma.CsmaHelper()
        ns3Nodes = ns.network.NodeContainer()
        if hasattr( node, 'nsNode' ) and node.nsNode is not None:
            # If it is assigned, go ahead.
            ns3Nodes.Add (node.nsNode)
            ns3Nodes.Create (1)
            pass
        else:
            # If not, create new ns-3 node and assign it to this Mininet node.
            # nodesContainer.Get(0) is tapbridge csma, nodeContainer.Get(1) is dual
            # interfaces node: csma and ue
            ns3Nodes.Create (2)
            node.nsNode = ns3Nodes.Get(0)
       
        allNodes.append( ns3Nodes.Get(0) )
        allNodes.append( ns3Nodes.Get(1) )

        mobility = ns.mobility.MobilityHelper()
        mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel")
        mobility.Install (ns3Nodes)

        devices = csma.Install (ns3Nodes)
        stack = ns.internet.InternetStackHelper ()
        stack.Install (ns3Nodes)
        addresses = ns.internet.Ipv4AddressHelper()
        addresses.SetBase (ns.network.Ipv4Address(networkAddress), ns.network.Ipv4Mask(netMask)) 
        interfaces = addresses.Assign (devices) 

        # set route default route for the tap-bridge
        ipv4RoutingHelper = ns.internet.Ipv4StaticRoutingHelper ()
        StaticRouting = ipv4RoutingHelper.GetStaticRouting (ns3Nodes.Get(0).GetObject(ns.internet.Ipv4.GetTypeId()))
        StaticRouting.SetDefaultRoute (interfaces.GetAddress (1), 1)
      
        # set static route for UE, it will have dual interfaces
        StaticRouting = ipv4RoutingHelper.GetStaticRouting (ns3Nodes.Get(1).GetObject(ns.internet.Ipv4.GetTypeId()))
        StaticRouting.AddNetworkRouteTo (ns.network.Ipv4Address (networkAddress), ns.network.Ipv4Mask (netMask),1)

       
        if port is None:
            # ...obtain it automatically.
            port = node.newPort()
         # If interface name is not specified...
        if intfName is None:
            # ...obtain it automatically.
            intfName = node.name + '-eth' + repr( port ) # classmethod
        # In the specified Mininet node, create TBIntf bridged with the 'device'.
        print ( intfName, node, port, node.nsNode, devices.Get (0), mode )
        tb = TBIntf( intfName, node, port, ns3Nodes.Get(0), devices.Get (0), mode )
        return ns3Nodes
 


def LteNetwork():

    info( '*** ns-3 network demo\n' )
    net = Mininet( controller=OVSController )

    info( '*** Adding controller\n' )
    net.addController( 'c0' )

    info( '*** Creating Mininet host \n' )
    h1 = net.addHost( 'h1', ip='7.1.0.3' )
    h2 = net.addHost( 'h2', ip='7.2.0.3' )

    UeGatewayNodes = ns.network.NodeContainer()
    #ueNetDevices = ns.network.NetDeviceContainer()
    #ueIfaces = ns.internet.Ipv4InterfaceContainer()

    ue1 = UeNode(h1,"7.1.0.0","255.255.255.0")
    UeGatewayNodes.Add(ue1.Get(0))
    ue1 = UeNode(h2,"7.2.0.0","255.255.255.0")
    UeGatewayNodes.Add(ue1.Get(0))

    #UeGatewayNodes.Add(UeNode.AddUe(h1,"7.1.0.0","255.255.255.0"))
    #UeGatewayNodes.Add(UeNode.AddUe(h2,"7.2.0.0","255.255.255.0"))

    lteHelper = ns.lte.LteHelper ()
    epcHelper = ns.lte.PointToPointEpcHelper()
    lteHelper.SetEpcHelper(epcHelper)
    lteHelper.SetSchedulerType("ns3::RrFfMacScheduler")
    lteHelper.SetEnbAntennaModelType("ns3::IsotropicAntennaModel")

    pgw = epcHelper.GetPgwNode ()

    enbNodes = ns.network.NodeContainer()
    enbNodes.Create(1)  
    mobility = ns.mobility.MobilityHelper()
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel")
    mobility.Install (enbNodes)

    enbLteDevs = lteHelper.InstallEnbDevice (enbNodes)
    UeLteDevs = lteHelper.InstallUeDevice (UeGatewayNodes)
    UeIpIfaces = epcHelper.AssignUeIpv4Address (ns.network.NetDeviceContainer (UeLteDevs))
  
    ipv4RoutingHelper = ns.internet.Ipv4StaticRoutingHelper ()
    for i in range(0, UeGatewayNodes.GetN()):
        UeStaticRouting = ipv4RoutingHelper.GetStaticRouting  (UeGatewayNodes.Get(i).GetObject(ns.internet.Ipv4.GetTypeId()))
        UeStaticRouting.SetDefaultRoute (epcHelper.GetUeDefaultGatewayAddress (), 2)


    UeStaticRouting = ipv4RoutingHelper.GetStaticRouting  (UeGatewayNodes.Get(0).GetObject(ns.internet.Ipv4.GetTypeId()))
    UeStaticRouting.AddNetworkRouteTo (ns.network.Ipv4Address ("7.2.0.0"), ns.network.Ipv4Mask ("255.255.255.0"),2);
    

    UeStaticRouting = ipv4RoutingHelper.GetStaticRouting  (UeGatewayNodes.Get(1).GetObject(ns.internet.Ipv4.GetTypeId()))
    UeStaticRouting.AddNetworkRouteTo (ns.network.Ipv4Address ("7.1.0.0"), ns.network.Ipv4Mask ("255.255.255.0"),2)

    for i in range(0,UeLteDevs.GetN()):
        lteHelper.Attach (UeLteDevs.Get(i), enbLteDevs.Get(0))

    for x in range(0,UeGatewayNodes.GetN()):
        node = UeGatewayNodes.Get(x)
        nd = node.GetDevice(0)
        arpL3 = node.GetObject(ns.internet.ArpL3Protocol.GetTypeId())
        arpcache = arpL3.FindCache(nd)
        #arpcache.SetAliveTimeout(ns.core.Seconds(default_duration)


    net.start()
    start()
 
    info( '*** Running CLI\n' )
    CLI( net )

    info( '*** Stopping network' )
    clear()                     # line added
    net.stop() 

if __name__ == '__main__':
   setLogLevel( 'info' )

   LteNetwork()



























