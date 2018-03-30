/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */


#include <iostream>
#include <fstream>
#include <string>
#include <cassert>

#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "ns3/applications-module.h"
#include "ns3/wifi-module.h"
#include "ns3/mesh-module.h"
#include "ns3/mobility-module.h"
#include "ns3/mesh-helper.h"
#include "ns3/mesh-module.h"
#include "ns3/wifi-phy.h"
#include "ns3/csma-module.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("MeshTap");


int
main (int argc, char *argv[])
{

    Packet::EnablePrinting();

    LogComponentEnable("MeshTap",LOG_LEVEL_ALL);
    LogComponentEnable("MeshTap",LOG_PREFIX_ALL);

    LogComponentEnable ("LtePacketSink", LOG_LEVEL_INFO);
    LogComponentEnable ("LtePacketSink", LOG_PREFIX_ALL); 

    LogComponentEnable ("LtePacketSource", LOG_LEVEL_INFO);
    LogComponentEnable ("LtePacketSource", LOG_PREFIX_ALL); 


    LogComponentEnable ("Ipv4L3Protocol", LOG_LEVEL_ALL);
    LogComponentEnable ("Ipv4L3Protocol", LOG_PREFIX_ALL); 
 // LogComponentEnable ("HwmpProtocolMac", LOG_LEVEL_ALL);
 // LogComponentEnable ("HwmpProtocolMac", LOG_PREFIX_ALL);
   
   //LogComponentEnable ("HwmpTcpInterface", LOG_LEVEL_INFO);
   //LogComponentEnable ("HwmpTcpInterface", LOG_PREFIX_ALL);

 //  LogComponentEnable ("HwmpProtocol", LOG_LEVEL_ALL);
 //  LogComponentEnable ("HwmpProtocol", LOG_PREFIX_ALL);
 //LogComponentEnable ("ArpL3Protocol", LOG_LEVEL_ALL);
 //LogComponentEnable ("ArpL3Protocol", LOG_PREFIX_ALL); 

 LogComponentEnable ("TcpL4Protocol", LOG_LEVEL_ALL);
 LogComponentEnable ("TcpL4Protocol", LOG_PREFIX_ALL); 
 LogComponentEnable ("TcpSocketBase", LOG_LEVEL_ALL);
 LogComponentEnable ("TcpSocketBase", LOG_PREFIX_ALL);


 
 /* ********************* Setup wireless mesh first ***************************** */   
  std::string m_root;
  m_root ="ff:ff:ff:ff:ff:ff";
  int m_grid=2;


  // Here, we will explicitly create four nodes.
  NS_LOG_INFO ("Create nodes.");
  NodeContainer meshNodes;
  meshNodes.Create(m_grid*m_grid);

  YansWifiPhyHelper wifiPhy = YansWifiPhyHelper::Default ();
  wifiPhy.Set ("EnergyDetectionThreshold", DoubleValue (-89.0) );
  wifiPhy.Set ("CcaMode1Threshold", DoubleValue (-62.0) );
  wifiPhy.Set ("TxGain", DoubleValue (1.0) );
  wifiPhy.Set ("RxGain", DoubleValue (1.0) );
  wifiPhy.Set ("TxPowerLevels", UintegerValue (1) );
  wifiPhy.Set ("TxPowerEnd", DoubleValue (18.0) );
  wifiPhy.Set ("TxPowerStart", DoubleValue (18.0) );
  wifiPhy.Set ("RxNoiseFigure", DoubleValue (7.0) );

  YansWifiChannelHelper wifiChannel = YansWifiChannelHelper::Default ();
  wifiPhy.SetChannel (wifiChannel.Create ());
  
  MeshHelper mesh = MeshHelper::Default ();
  if (!Mac48Address (m_root.c_str ()).IsBroadcast ())
    {
      mesh.SetStackInstaller ("ns3::Dot11sStack", "Root", Mac48AddressValue (Mac48Address (m_root.c_str ())));
    }
  else
    {
      mesh.SetStackInstaller ("ns3::Dot11sStack");
    }
  mesh.SetSpreadInterfaceChannels (MeshHelper::ZERO_CHANNEL);
  mesh.SetMacType ("RandomStart", TimeValue (Seconds (0.1)));
  mesh.SetStandard (WIFI_PHY_STANDARD_80211g);
  mesh.SetRemoteStationManager ("ns3::ConstantRateWifiManager", "DataMode", StringValue ("ErpOfdmRate6Mbps"), "RtsCtsThreshold", UintegerValue (2500));
 

 
  // Install protocols and return container if MeshPointDevices
  NetDeviceContainer meshDevices = mesh.Install (wifiPhy, meshNodes);

  // Setup mobility - static grid topology
  MobilityHelper mobility;
  mobility.SetPositionAllocator ("ns3::GridPositionAllocator",
                                 "MinX", DoubleValue (200.0),
                                 "MinY", DoubleValue (100.0),
                                 "DeltaX", DoubleValue (100.0),
                                 "DeltaY", DoubleValue (100.0),
                                 "GridWidth", UintegerValue (m_grid),
                                 "LayoutType", StringValue ("RowFirst"));
  mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
  mobility.Install (meshNodes);

  InternetStackHelper stack;
  stack.Install (meshNodes);

  Ipv4AddressHelper address2;
  address2.SetBase ("7.3.0.0","255.255.255.0");
  Ipv4InterfaceContainer interMesh = address2.Assign (meshDevices);

  /* ***************** end of wireless mesh setup ***************************** 

         ************* Setup csma nodes left and right **************
   */

  int meshIdLeft = 0;
  int meshIdRight = 1;

  CsmaHelper csma;
  csma.SetChannelAttribute ("DataRate", DataRateValue (DataRate (5000000)));
  csma.SetChannelAttribute ("Delay", TimeValue (MilliSeconds (2)));

  NodeContainer csmaTapNodes;
  csmaTapNodes.Create(2);

  NodeContainer csmaLeftNodes;
  NodeContainer csmaRightNodes;
  NodeContainer csmaMeshNodes;

  csmaLeftNodes.Add(csmaTapNodes.Get(0));
  csmaRightNodes.Add(csmaTapNodes.Get(1));

  csmaMeshNodes.Add(meshNodes.Get(meshIdLeft));  
  csmaMeshNodes.Add(meshNodes.Get(meshIdRight));
  
  csmaLeftNodes.Add(csmaMeshNodes.Get(0));
  csmaRightNodes.Add(csmaMeshNodes.Get(1));

  mobility.Install( csmaTapNodes);
  stack.Install (csmaTapNodes);

  NetDeviceContainer csmaDevicesLeft = csma.Install (csmaLeftNodes);
  Ipv4AddressHelper address;
  address.SetBase ("7.1.0.0","255.255.255.0");
  Ipv4InterfaceContainer interfacesLeft = address.Assign (csmaDevicesLeft);
  

  NetDeviceContainer csmaDevicesRight = csma.Install (csmaRightNodes);
  address.SetBase ("7.2.0.0","255.255.255.0");
  Ipv4InterfaceContainer interfacesRight = address.Assign (csmaDevicesRight);

 
  /* ********** Collect IP-MAC pairs from the left, right, and mesh nodes ********************* */

  typedef std::pair<Mac48Address, Ipv4Address> AddressMapping;
  int x = 0;
  Mac48Address mac;
  Ptr<NetDevice> nd_sink;
  Ptr<CsmaNetDevice> csmaNode;
  std::vector <AddressMapping> m_ArpCsmaLeft;
  for (NetDeviceContainer::Iterator i = csmaDevicesLeft.Begin (); i != csmaDevicesLeft.End (); ++i)
   {
      Ptr<CsmaNetDevice> cp = (*i)->GetObject<CsmaNetDevice> ();
      //Ptr<NetDevice> nd = *i;
      mac = Mac48Address::ConvertFrom (cp->GetAddress () );
      AddressMapping arp = std::make_pair (Mac48Address::ConvertFrom (cp->GetAddress () ), interfacesLeft.GetAddress (x) );
      m_ArpCsmaLeft.push_back (arp);
      std::cout << Mac48Address::ConvertFrom (cp->GetAddress ()) << "," << interfacesLeft.GetAddress (x) << std::endl;
      
      x++;
   }


  x = 0;
  std::vector <AddressMapping> m_ArpCsmaRight;
  for (NetDeviceContainer::Iterator i = csmaDevicesRight.Begin (); i != csmaDevicesRight.End (); ++i)
   {
      Ptr<CsmaNetDevice> cp = (*i)->GetObject<CsmaNetDevice> ();
      //Ptr<NetDevice> nd = *i;
      mac = Mac48Address::ConvertFrom (cp->GetAddress () );
      AddressMapping arp = std::make_pair (Mac48Address::ConvertFrom (cp->GetAddress () ), interfacesRight.GetAddress (x) );
      m_ArpCsmaRight.push_back (arp);
      std::cout << Mac48Address::ConvertFrom (cp->GetAddress ()) << "," << interfacesRight.GetAddress (x) << std::endl;
      
      x++;
   }


  x = 0;
  std::vector <AddressMapping> m_ArpMesh;
  for (NetDeviceContainer::Iterator i = meshDevices.Begin (); i != meshDevices.End (); ++i)
   {
      Ptr<MeshPointDevice> cp = (*i)->GetObject<MeshPointDevice> ();
      //Ptr<NetDevice> nd = *i;
      mac = Mac48Address::ConvertFrom (cp->GetAddress () );
      AddressMapping arp = std::make_pair (Mac48Address::ConvertFrom (cp->GetAddress () ), interMesh.GetAddress (x) );
      m_ArpMesh.push_back (arp);
      std::cout << Mac48Address::ConvertFrom (cp->GetAddress ()) << "," << interMesh.GetAddress (x) << std::endl;
      
      x++;
   }


  for (NetDeviceContainer::Iterator i = csmaDevicesLeft.Begin (); i != csmaDevicesLeft.End (); ++i)
   {
      Ptr<CsmaNetDevice> cp = (*i)->GetObject<CsmaNetDevice> ();
      Ptr<NetDevice> nd = *i;
      Ptr<Node> node = cp->GetNode ();
      Ptr<ArpL3Protocol> arpL3 = node->GetObject<ArpL3Protocol> ();
      Ptr<ArpCache> arpcache = arpL3->FindCache (nd);
      arpcache->SetAliveTimeout(Seconds(36000));
      for (long index = 0; index < (long) m_ArpCsmaRight.size (); index++ ) {
              ArpCache::Entry *entry = arpcache->Lookup (m_ArpCsmaRight.at(index).second);
              if (entry == 0 ) {
                    NS_LOG_LOGIC ("Add new entry to the ARP cache" );
                    entry = arpcache->Add (m_ArpCsmaRight.at(index).second);
              }
              entry->SetMacAddress (m_ArpCsmaRight.at(index).first);
              std::cout << node->GetId() << " , " << Mac48Address::ConvertFrom( m_ArpCsmaRight.at(index).first) << "," << m_ArpCsmaRight.at(index).second << std::endl;

      }
      for (long index = 0; index < (long) m_ArpMesh.size (); index++ ) {
              ArpCache::Entry *entry = arpcache->Lookup (m_ArpMesh.at(index).second);
              if (entry == 0 ) {
                    NS_LOG_LOGIC ("Add new entry to the ARP cache" );
                    entry = arpcache->Add (m_ArpMesh.at(index).second);
              }
              entry->SetMacAddress (m_ArpMesh.at(index).first);
              std::cout << node->GetId() << " , " << Mac48Address::ConvertFrom(m_ArpMesh.at(index).first) << "," << m_ArpMesh.at(index).second << std::endl;

      }

   }

   for (NetDeviceContainer::Iterator i = csmaDevicesRight.Begin (); i != csmaDevicesRight.End (); ++i)
   {
      Ptr<CsmaNetDevice> cp = (*i)->GetObject<CsmaNetDevice> ();
      Ptr<NetDevice> nd = *i;
      Ptr<Node> node = cp->GetNode ();
      Ptr<ArpL3Protocol> arpL3 = node->GetObject<ArpL3Protocol> ();
      Ptr<ArpCache> arpcache = arpL3->FindCache (nd);
      arpcache->SetAliveTimeout(Seconds(36000));
      for (long index = 0; index < (long) m_ArpCsmaLeft.size (); index++ ) {
              ArpCache::Entry *entry = arpcache->Lookup (m_ArpCsmaLeft.at(index).second);
              if (entry == 0 ) {
                    NS_LOG_LOGIC ("Add new entry to the ARP cache" );
                    entry = arpcache->Add (m_ArpCsmaLeft.at(index).second);
              }
              entry->SetMacAddress (m_ArpCsmaLeft.at(index).first);   
        std::cout << node->GetId() << " , " << m_ArpCsmaLeft.at(index).first << " , " << m_ArpCsmaLeft.at(index).second << std::endl;

      }
      for (long index = 0; index < (long) m_ArpMesh.size (); index++ ) {
              ArpCache::Entry *entry = arpcache->Lookup (m_ArpMesh.at(index).second);
              if (entry == 0 ) {
                    NS_LOG_LOGIC ("Add new entry to the ARP cache" );
                    entry = arpcache->Add (m_ArpMesh.at(index).second);
              }
              entry->SetMacAddress (m_ArpMesh.at(index).first);
              std::cout << node->GetId() << " , " << m_ArpMesh.at(index).first << " , " << m_ArpMesh.at(index).second << std::endl;

      }

   }

   Ipv4StaticRoutingHelper ipv4RoutingHelper;
  
   Ptr<Ipv4StaticRouting> csmaTapStaticRouting = ipv4RoutingHelper.GetStaticRouting(csmaTapNodes.Get(0)->GetObject<Ipv4> ());
   csmaTapStaticRouting->AddNetworkRouteTo (Ipv4Address("7.2.0.0"),Ipv4Mask("255.255.255.0"), 1);
   csmaTapStaticRouting->AddNetworkRouteTo (Ipv4Address("7.3.0.0"),Ipv4Mask("255.255.255.0"), 1);

   Ptr<Ipv4StaticRouting> csmaTap2StaticRouting = ipv4RoutingHelper.GetStaticRouting(csmaTapNodes.Get(1)->GetObject<Ipv4> ());
   csmaTap2StaticRouting->AddNetworkRouteTo (Ipv4Address("7.1.0.0"),Ipv4Mask("255.255.255.0"), 1);
   csmaTap2StaticRouting->AddNetworkRouteTo (Ipv4Address("7.3.0.0"),Ipv4Mask("255.255.255.0"), 1);

   Ptr<Ipv4StaticRouting> csmaMeshStaticRouting = ipv4RoutingHelper.GetStaticRouting(csmaMeshNodes.Get(0)->GetObject<Ipv4> ());
   csmaMeshStaticRouting->AddNetworkRouteTo (Ipv4Address("7.2.0.0"),Ipv4Mask("255.255.255.0"), 2);
   csmaMeshStaticRouting->AddNetworkRouteTo (Ipv4Address("7.1.0.0"),Ipv4Mask("255.255.255.0"), 1);

   Ptr<Ipv4StaticRouting> csmaMesh2StaticRouting = ipv4RoutingHelper.GetStaticRouting(csmaMeshNodes.Get(1)->GetObject<Ipv4> ());
   csmaMesh2StaticRouting->AddNetworkRouteTo (Ipv4Address("7.1.0.0"),Ipv4Mask("255.255.255.0"), 2);
   csmaMesh2StaticRouting->AddNetworkRouteTo (Ipv4Address("7.2.0.0"),Ipv4Mask("255.255.255.0"), 1);



  int m_dest_port=3000;
  std::string m_protocol = "ns3::TcpSocketFactory";

  InetSocketAddress dst = InetSocketAddress (interfacesRight.GetAddress (0), m_dest_port);
  Ptr<Node> source = csmaTapNodes.Get(0);
  Ptr<Node> sinkNode = csmaTapNodes.Get(1);

/*  between mesh nodes

  InetSocketAddress dst = InetSocketAddress (interMesh.GetAddress (2), m_dest_port);
  Ptr<Node> source = meshNodes.Get(0);
  Ptr<Node> sinkNode = meshNodes.Get(2);
*/


  LtePacketSourceHelper onoff (m_protocol, Address (dst));
  onoff.SetAttribute ("PacketSize", UintegerValue (1024));
  onoff.SetAttribute ("FirstSendingTime", TimeValue (Seconds(2.0)));
  onoff.SetAttribute ("Interval", TimeValue (Seconds(5.0)));



  ApplicationContainer apps = onoff.Install (source);
  apps.Start (Seconds (1.0));
  apps.Stop (Seconds (10.0));

  NS_LOG_INFO ("Create Sink.");
  LtePacketSinkHelper sink (m_protocol,dst);
  sink.SetAttribute ("DefaultRxSize", UintegerValue(1024));
  ApplicationContainer receiver = sink.Install (sinkNode);
  receiver.Start (Seconds (0.0));
  receiver.Stop (Seconds (11.0));

 //Simulator::Schedule (Seconds (m_totalTime), &MeshTest::Report, this);
  Simulator::Stop (Seconds (25));

  Simulator::Run();
  Simulator::Destroy();

  NS_LOG_INFO ("Done.");
  return 0;





/*
 



 



 
        


//csmaMesh2StaticRouting->AddNetworkRouteTo (Ipv4Address("7.3.0.0"),Ipv4Mask("255.255.255.0"), 2);



  Ipv4InterfaceAddress iaddr = csmaMeshNodes.Get(0)->GetObject<Ipv4>()->GetAddress (1,0);
  Ipv4Address addri = iaddr.GetLocal (); 
  std::cout << "CSMA-MESH Left IP address 1 : " << addri << " " << csmaMeshNodes.Get(0)->GetObject<Ipv4>()->GetInterfaceForAddress (addri) << "Node ID : " << csmaMeshNodes.Get(0)->GetId () << std::endl;   

 
  iaddr = csmaMeshNodes.Get(0)->GetObject<Ipv4>()->GetAddress (2,0);
  addri = iaddr.GetLocal (); 
  std::cout << "CSMA-MESH Left IP address 2 : " << addri << " " << csmaMeshNodes.Get(0)->GetObject<Ipv4>()->GetInterfaceForAddress (addri) << "Node ID : " << csmaMeshNodes.Get(0)->GetId () << std::endl;   


  iaddr = csmaMeshNodes.Get(1)->GetObject<Ipv4>()->GetAddress (1,0);
  addri = iaddr.GetLocal (); 
  std::cout << "CSMA-MESH right IP address 1 : " << addri << " " << csmaMeshNodes.Get(1)->GetObject<Ipv4>()->GetInterfaceForAddress (addri) << "Node ID : " << csmaMeshNodes.Get(1)->GetId () << std::endl;   

  iaddr = csmaMeshNodes.Get(1)->GetObject<Ipv4>()->GetAddress (2,0);
  addri = iaddr.GetLocal (); 
  std::cout << "CSMA-MESH right IP address 2 : " << addri << " " << csmaMeshNodes.Get(1)->GetObject<Ipv4>()->GetInterfaceForAddress (addri) << "Node ID : " << csmaMeshNodes.Get(1)->GetId () << std::endl;   

  iaddr = csmaTapNodes.Get(0)->GetObject<Ipv4>()->GetAddress (1,0);
  addri = iaddr.GetLocal (); 
  std::cout << "CSMA-Tap Left IP address 1 : " << addri << " " << csmaTapNodes.Get(0)->GetObject<Ipv4>()->GetInterfaceForAddress (addri) << "Node ID : " << csmaTapNodes.Get(0)->GetId () << std::endl;   

 
  //iaddr = csmaTapNodes.Get(0)->GetObject<Ipv4>()->GetAddress (2,0);
  //addri = iaddr.GetLocal (); 
  //std::cout << "CSMA-Tap Left IP address 2 : " << addri << " " << csmaTapNodes.Get(0)->GetObject<Ipv4>()->GetInterfaceForAddress (addri) << "Node ID : " << csmaTapNodes.Get(0)->GetId () << std::endl; 

  iaddr = csmaTapNodes.Get(1)->GetObject<Ipv4>()->GetAddress (1,0);
  addri = iaddr.GetLocal (); 
  std::cout << "CSMA-Tap Right IP address 1 : " << addri << " " << csmaTapNodes.Get(1)->GetObject<Ipv4>()->GetInterfaceForAddress (addri) << "Node ID : " << csmaTapNodes.Get(1)->GetId () << std::endl; 


*/

}

