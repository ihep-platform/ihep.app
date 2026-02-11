import Link from 'next/link';
import { Facebook, Twitter, Instagram, MapPin, Phone, Mail } from 'lucide-react';
import { APP_NAME } from '@/lib/constants';

const Footer = () => {
  return (
    <footer className="bg-primary text-white py-8">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-8">
          <div>
            <h3 className="font-montserrat font-bold text-lg mb-4">{APP_NAME}</h3>
            <p className="text-sm text-gray-300">
              Empowering patients with resources, support, and community connections since 2020.
            </p>
            <div className="flex mt-4 space-x-4">
              <a href="#" className="text-white hover:text-accent">
                <Facebook size={20} />
              </a>
              <a href="#" className="text-white hover:text-accent">
                <Twitter size={20} />
              </a>
              <a href="#" className="text-white hover:text-accent">
                <Instagram size={20} />
              </a>
            </div>
          </div>
          
          <div>
            <h3 className="font-montserrat font-bold text-md mb-4">Quick Links</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <div>
                  <Link href="/">
                    <div className="text-gray-300 hover:text-white cursor-pointer">Home</div>
                  </Link>
                </div>
              </li>
              <li>
                <div>
                  <Link href="/resources">
                    <div className="text-gray-300 hover:text-white cursor-pointer">Resources</div>
                  </Link>
                </div>
              </li>
              <li>
                <div>
                  <Link href="/events">
                    <div className="text-gray-300 hover:text-white cursor-pointer">Events</div>
                  </Link>
                </div>
              </li>
              <li>
                <div>
                  <Link href="/community">
                    <div className="text-gray-300 hover:text-white cursor-pointer">Community</div>
                  </Link>
                </div>
              </li>
              <li>
                <div>
                  <Link href="/education">
                    <div className="text-gray-300 hover:text-white cursor-pointer">Education</div>
                  </Link>
                </div>
              </li>
            </ul>
          </div>
          
          <div>
            <h3 className="font-montserrat font-bold text-md mb-4">Support</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <div>
                  <Link href="/help">
                    <div className="text-gray-300 hover:text-white cursor-pointer">Help Center</div>
                  </Link>
                </div>
              </li>
              <li>
                <div>
                  <Link href="/contact">
                    <div className="text-gray-300 hover:text-white cursor-pointer">Contact Us</div>
                  </Link>
                </div>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-montserrat font-bold text-md mb-4">Investors</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <div>
                  <Link href="/investor-dashboard">
                    <div className="text-gray-300 hover:text-white cursor-pointer">Investor Dashboard</div>
                  </Link>
                </div>
              </li>
              <li>
                <div>
                  <a href="/docs/ihep-pitch-deck.pdf" target="_blank" rel="noopener noreferrer">
                    <div className="text-gray-300 hover:text-white cursor-pointer">Investor Deck</div>
                  </a>
                </div>
              </li>
              <li>
                <div>
                  <a href="/docs/A%20Recursive%20Blueprint%20for%20a%20Global%20Problem.pdf" target="_blank" rel="noopener noreferrer">
                    <div className="text-gray-300 hover:text-white cursor-pointer">One-Page Overview</div>
                  </a>
                </div>
              </li>
              <li>
                <div>
                  <a href="/docs/IHEP%20Comprehensive%20Financial%20Model.pdf" target="_blank" rel="noopener noreferrer">
                    <div className="text-gray-300 hover:text-white cursor-pointer">Financial Model</div>
                  </a>
                </div>
              </li>
              <li>
                <div>
                  <a href="/docs/IHEP%20System%20Architecture%20Document.pdf" target="_blank" rel="noopener noreferrer">
                    <div className="text-gray-300 hover:text-white cursor-pointer">Technical Architecture</div>
                  </a>
                </div>
              </li>
              <li>
                <div>
                  <a href="/docs/IHEP%20Phase%20I%20Detailed%20Project%20Plan.pdf" target="_blank" rel="noopener noreferrer">
                    <div className="text-gray-300 hover:text-white cursor-pointer">Pilot Plan & Timeline</div>
                  </a>
                </div>
              </li>
              <li>
                <div>
                  <a href="/docs/IHEP%20Complete%20Due%20Diligence%20Package.pdf" target="_blank" rel="noopener noreferrer">
                    <div className="text-gray-300 hover:text-white cursor-pointer">Due Diligence Package</div>
                  </a>
                </div>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-montserrat font-bold text-md mb-4">Legal</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <div>
                  <Link href="/legal/terms">
                    <div className="text-gray-300 hover:text-white cursor-pointer">Terms of Service</div>
                  </Link>
                </div>
              </li>
              <li>
                <div>
                  <Link href="/legal/privacy">
                    <div className="text-gray-300 hover:text-white cursor-pointer">Privacy Policy</div>
                  </Link>
                </div>
              </li>
              <li>
                <div>
                  <Link href="/legal/ai-governance">
                    <div className="text-gray-300 hover:text-white cursor-pointer">AI Governance</div>
                  </Link>
                </div>
              </li>
              <li>
                <div>
                  <Link href="/legal/trust">
                    <div className="text-gray-300 hover:text-white cursor-pointer">Trust Statement</div>
                  </Link>
                </div>
              </li>
            </ul>
          </div>
          
          <div>
            <h3 className="font-montserrat font-bold text-md mb-4">Contact</h3>
            <ul className="space-y-2 text-sm">
              <li className="flex items-start">
                <Phone className="text-accent mr-2 h-4 w-4 mt-0.5" />
                <span className="text-gray-300">(917) 566-8112</span>
              </li>
              <li className="flex items-start">
                <Mail className="text-accent mr-2 h-4 w-4 mt-0.5" />
                <span className="text-gray-300">support@healthinsightventures.com</span>
              </li>
              <li className="flex items-start mt-2">
                <MapPin className="text-accent mr-2 h-4 w-4 mt-0.5" />
                <span className="text-gray-300">12 W 129th St, 1E, New York, NY 10027</span>
              </li>
              <li className="flex items-start mt-2">
                <Phone className="text-accent mr-2 h-4 w-4 mt-0.5" />
                <span className="text-gray-300">24/7 Support Available</span>
              </li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-gray-700 mt-8 pt-6 text-center text-sm text-gray-400">
          <p>© {new Date().getFullYear()} {APP_NAME}. All rights reserved. This website is HIPAA compliant and uses secure encryption.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
