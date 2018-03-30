""" Network topology
          
            
                                                   +-------+       +-----------+
                                                   |  EPC  +-------+ RemoteHost|
                                                   +-------        +-----------+
                                                       |
                                                       |
                                      +---------+      |
                                      |eNB      |------+ 
                                      |Base     |
                                      |Station  |
                                      +---------+
                                          |  |
                                          |  |
                   ns-3         ns-3      |  |     ns-3         ns-3
                   n0            n1       |  |      n1           n0
               +--------+    +--------+   |  |   +-------+    +-------+
               |        |    |        |   |  |   |       |    |       |
               |        |    |        |   |  |   |       |    |       |
               +--------+    +----+---+   |  |   +--+----+    +-------+
               |  CSMA  |----|CSMA|UE | --+  +---|UE|CSMA|----| CSMA  |
               +--------+    +----+---+          +--+----+    +-------+
                   
               |<-------------------------------------------------->|
                                     ns-3 process
                                 in the root namespace

 The CSMA device on node zero is:  X.Y.0.1
 The CSMA device on node one is:   X.Y.0.2
 The CSMA device on node two is:   X.Z.0.3
 The CSMA device on node three is: X.Z.0.4
 Remote Host : 10.X.Y.Z
"""
#include "ns3/ipv4-global-routing-helper.h"

import sys

import ns.applications
import ns.core
import ns.csma
import ns.internet
import ns.network
import ns.tap_bridge
import ns.wifi
import ns.lte
import ns.point_to_point


def main(argv):

    #ns.core.GlobalValue.Bind ("SimulatorImplementationType", ns.core.StringValue ("ns3::RealtimeSimulatorImpl"))
    #ns.core.GlobalValue.Bind ("ChecksumEnabled", ns.core.BooleanValue ("true"))
 
    ns.core.LogComponentEnable("EpcSgwPgwApplication",ns.core.LOG_LEVEL_INFO)
    ns.core.LogComponentEnable("EpcSgwPgwApplication",ns.core.LOG_PREFIX_NODE)
    #ns.core.LogComponentEnable("OnOffApplication",ns.core.LOG_LEVEL_INFO)
    #ns.core.LogComponentEnable("PacketSink",ns.core.LOG_LEVEL_INFO)  

    
    #ns.core.LogComponentEnable("OnOffApplication",ns.core.LOG_PREFIX_NODE)
    #ns.core.LogComponentEnable("PacketSink",ns.core.LOG_PREFIX_NODE)  

    #ns.core.LogComponentEnable ("LteUeNetDevice", ns.core.LOG_LEVEL_INFO)
    #ns.core.LogComponentEnable ("LteUeNetDevice", ns.core.LOG_PREFIX_NODE)

    #ns.core.LogComponentEnable ("V4Ping", ns.core.LOG_LEVEL_INFO)
    #ns.core.LogComponentEnable ("V4Ping", ns.core.LOG_PREFIX_NODE)
    
    #ns.core.LogComponentEnable ("Ipv4L3Protocol", ns.core.LOG_LEVEL_ALL)
    #ns.core.LogComponentEnable ("Ipv4L3Protocol", ns.core.LOG_PREFIX_NODE)
    ns.core.LogComponentEnable ("UdpEchoServerApplication", ns.core.LOG_LEVEL_INFO)
    ns.core.LogComponentEnable ("UdpEchoServerApplication", ns.core.LOG_PREFIX_NODE)
    ns.core.LogComponentEnable ("UdpEchoClientApplication", ns.core.LOG_LEVEL_INFO)
    ns.core.LogComponentEnable ("UdpEchoClientApplication", ns.core.LOG_PREFIX_NODE)


    #ns.core.LogComponentEnable ("Ipv4L3Protocol", ns.core.LOG_PREFIX_FUNC)

    #ns.core.LogComponentEnable ("Ipv4ListRouting", ns.core.LOG_LEVEL_ALL)
    #ns.core.LogComponentEnable ("Ipv4ListRouting", ns.core.LOG_PREFIX_NODE)

    csma1Nodes = ns.network.NodeContainer()
    csma1Nodes.Create (2);

    csma = ns.csma.CsmaHelper()
    csma1NetDevices = csma.Install (csma1Nodes)

    stack = ns.internet.InternetStackHelper ()
    stack.Install (csma1Nodes)
    addresses = ns.internet.Ipv4AddressHelper()
    addresses.SetBase (ns.network.Ipv4Address("7.1.0.0"), ns.network.Ipv4Mask("255.255.255.0"))
    #csma1Interfaces = ns.internet.Ipv4IterfaceContainer ()
    csma1Interfaces = addresses.Assign (csma1NetDevices)
    for i in range(0,csma1Nodes.GetN()):
        print "CSMA 1 Node Id %s and IP address %s " %(csma1Nodes.Get(i).GetId() , csma1Interfaces.GetAddress(i))


    csma2Nodes = ns.network.NodeContainer()
    csma2Nodes.Create (2);

    csma = ns.csma.CsmaHelper()
    csma2NetDevices = csma.Install (csma2Nodes)

    stack = ns.internet.InternetStackHelper ()
    stack.Install (csma2Nodes)
    addresses = ns.internet.Ipv4AddressHelper()
    addresses.SetBase (ns.network.Ipv4Address("7.2.0.0"), ns.network.Ipv4Mask("255.255.255.0"))
    #csma1Interfaces = ns.internet.Ipv4IterfaceContainer ()
    csma2Interfaces = addresses.Assign (csma2NetDevices)

    for i in range(0,csma2Nodes.GetN()):
        print "CSMA 2 Node Id %s and IP address %s " %(csma2Nodes.Get(i).GetId() , csma2Interfaces.GetAddress(i))

    csmaOneGateway = csma1Nodes.Get (1)
    csmaTwoGateway = csma2Nodes.Get (1)

    
    lteHelper = ns.lte.LteHelper ()
    epcHelper = ns.lte.PointToPointEpcHelper()
    lteHelper.SetEpcHelper(epcHelper)
    lteHelper.SetSchedulerType("ns3::RrFfMacScheduler")
    lteHelper.SetEnbAntennaModelType("ns3::IsotropicAntennaModel")

    pgw = epcHelper.GetPgwNode ()

    
    remoteHostContainer = ns.network.NodeContainer()
    remoteHostContainer.Create(1)
    remoteHost = remoteHostContainer.Get (0)
   
    csmaUeNodes = ns.network.NodeContainer()
    csmaUeNodes.Add (csmaOneGateway)
    csmaUeNodes.Add (csmaTwoGateway)

    enbNodes = ns.network.NodeContainer()
    enbNodes.Create(1)
   
    mobility = ns.mobility.MobilityHelper()
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel")

    mobility.Install (csmaUeNodes)
    mobility.Install (enbNodes)

    p2ph = ns.point_to_point.PointToPointHelper ()
    p2ph.SetDeviceAttribute ("DataRate", ns.network.DataRateValue (ns.network.DataRate ("100Gb/s")))
    p2ph.SetDeviceAttribute ("Mtu", ns.core.UintegerValue (1500))
    p2ph.SetChannelAttribute ("Delay", ns.core.TimeValue (ns.core.Seconds (0.010)))

    internetDevices = p2ph.Install (pgw, remoteHost)
    stack.Install (remoteHostContainer)

    addresses.SetBase (ns.network.Ipv4Address("10.1.4.0"), ns.network.Ipv4Mask("255.255.255.0"))
    internetIpIfaces = addresses.Assign (internetDevices)
    remoteHostAddr = internetIpIfaces.GetAddress (1)
    print "Remote Host Address %s " %remoteHostAddr

    ipv4RoutingHelper = ns.internet.Ipv4StaticRoutingHelper ()
    remoteHostStaticRouting = ipv4RoutingHelper.GetStaticRouting(remoteHost.GetObject(ns.internet.Ipv4.GetTypeId()))
    remoteHostStaticRouting.AddNetworkRouteTo (ns.network.Ipv4Address ("10.1.4.0"), ns.network.Ipv4Mask ("255.255.255.0"), 1)
    remoteHostStaticRouting.AddNetworkRouteTo (ns.network.Ipv4Address ("7.0.0.0"), ns.network.Ipv4Mask ("255.0.0.0"), 1)


    enbLteDevs = lteHelper.InstallEnbDevice (enbNodes)
    meshUeLteDevs = lteHelper.InstallUeDevice (csmaUeNodes)

    meshUeIpIfaces = epcHelper.AssignUeIpv4Address (ns.network.NetDeviceContainer (meshUeLteDevs))
  
    meshUe1StaticRouting = ipv4RoutingHelper.GetStaticRouting  (csmaOneGateway.GetObject(ns.internet.Ipv4.GetTypeId()))
    meshUe1StaticRouting.SetDefaultRoute (epcHelper.GetUeDefaultGatewayAddress (), 2);
    meshUe1StaticRouting.AddNetworkRouteTo (ns.network.Ipv4Address ("10.1.4.0"), ns.network.Ipv4Mask ("255.255.255.0"),2);
    meshUe1StaticRouting.AddNetworkRouteTo (ns.network.Ipv4Address ("7.2.0.0"), ns.network.Ipv4Mask ("255.255.255.0"),2);
    meshUe1StaticRouting.AddNetworkRouteTo (ns.network.Ipv4Address ("7.1.0.0"), ns.network.Ipv4Mask ("255.255.255.0"),1);

  
    meshUe2StaticRouting = ipv4RoutingHelper.GetStaticRouting  (csmaTwoGateway.GetObject(ns.internet.Ipv4.GetTypeId()))
    meshUe2StaticRouting.SetDefaultRoute (epcHelper.GetUeDefaultGatewayAddress (), 2)
    meshUe2StaticRouting.AddNetworkRouteTo (ns.network.Ipv4Address ("10.1.4.0"), ns.network.Ipv4Mask ("255.255.255.0"),2)
    meshUe2StaticRouting.AddNetworkRouteTo (ns.network.Ipv4Address ("7.1.0.0"), ns.network.Ipv4Mask ("255.255.255.0"),2)
    meshUe2StaticRouting.AddNetworkRouteTo (ns.network.Ipv4Address ("7.2.0.0"), ns.network.Ipv4Mask ("255.255.255.0"),1)

    for i in range(0,meshUeLteDevs.GetN()):
        lteHelper.Attach (meshUeLteDevs.Get(i), enbLteDevs.Get(0))

    pgwStaticRouting = ipv4RoutingHelper.GetStaticRouting (pgw.GetObject(ns.internet.Ipv4.GetTypeId()))
    pgwStaticRouting.AddNetworkRouteTo (ns.network.Ipv4Address ("10.1.1.0"), ns.network.Ipv4Mask    ("255.255.255.0"), 3)

    for i in range(0,csma1Nodes.GetN()):
        meshStaticRouting = ipv4RoutingHelper.GetStaticRouting (csma1Nodes.Get(i).GetObject(ns.internet.Ipv4.GetTypeId()))
        meshStaticRouting.SetDefaultRoute (csma1Interfaces.GetAddress (1), 1)

        meshStaticRouting = ipv4RoutingHelper.GetStaticRouting (csma2Nodes.Get(i).GetObject(ns.internet.Ipv4.GetTypeId()))
        meshStaticRouting.SetDefaultRoute (csma2Interfaces.GetAddress (1), 1)

    remoteHostAddr = csma2Interfaces.GetAddress (0)
    remoteHost = csma2Nodes.Get(0)
    src = csma1Nodes.Get(0)
   
    echoServer = ns.applications.UdpEchoServerHelper(9)

    serverApps = echoServer.Install(remoteHost)
    serverApps.Start(ns.core.Seconds(1.0))
    serverApps.Stop(ns.core.Seconds(10.0))

    echoClient = ns.applications.UdpEchoClientHelper(remoteHostAddr, 9)
    echoClient.SetAttribute("MaxPackets", ns.core.UintegerValue(1))
    echoClient.SetAttribute("Interval", ns.core.TimeValue(ns.core.Seconds (1.0)))
    echoClient.SetAttribute("PacketSize", ns.core.UintegerValue(64))

    clientApps = echoClient.Install(src)
    clientApps.Start(ns.core.Seconds(2.0))
    clientApps.Stop(ns.core.Seconds(10.0))

      
    #InstallApplication(csma1Nodes,csma2Interfaces.GetAddress(1),csma2Nodes.Get(1), 3100, m_packetSize,  10, 5, 2,m_ac,  2)  


    
    ns.network.Packet.EnablePrinting ()
    
    ns.core.Simulator.Stop (ns.core.Seconds (20.))
    ns.core.Simulator.Run ()
    ns.core.Simulator.Destroy ()
    return 0

if __name__ == '__main__':
     #ns.core.LogComponentEnable("EpcSgwPgwApplication",ns.core.LOG_PREFIX_INFO)
     sys.exit(main(sys.argv))


