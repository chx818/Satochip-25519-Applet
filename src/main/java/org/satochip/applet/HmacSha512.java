/*
 * SatoChip Bitcoin Hardware Wallet based on javacard
 * (c) 2015 by Toporin - 16DMCk4WUaHofchAhpMaQS4UPm4urcy2dN
 * Sources available on https://github.com/Toporin  
 *               
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *   
 */    

package org.satochip.applet;

import javacard.framework.ISOException;
import javacard.framework.Util;
import javacard.security.MessageDigest;

// Compatibility HMAC-SHA512 implementation used by the original applet. The J3R452 profile does
// not expose a usable hardware HMAC engine, so this implementation intentionally has one path.
public class HmacSha512 {

    public static final short BLOCKSIZE=128; // 128 bytes 
    public static final short HASHSIZE=64;
    private static byte[] data;
    private static MessageDigest sha512;
    
    public static void init(byte[] tmp){
        data = tmp;
        sha512 = MessageDigest.getInstance(MessageDigest.ALG_SHA_512, false);
    }
    
    public static short computeHmacSha512(byte[] key, short key_offset, short key_length, 
            byte[] message, short message_offset, short message_length,
            byte[] mac, short mac_offset){
        
        if (key_length>BLOCKSIZE || key_length<0){
            ISOException.throwIt(Satochip.SW_HMAC_UNSUPPORTED_KEYSIZE); // don't accept keys bigger than block size 
        }

        if (sha512 == null) {
            ISOException.throwIt(Satochip.SW_UNSUPPORTED_FEATURE);
        }

        if (message_length>HASHSIZE || message_length<0){
            ISOException.throwIt(Satochip.SW_HMAC_UNSUPPORTED_MSGSIZE); // don't accept message bigger than block size (should be sufficient for BIP32)
        }

        try {
            // compute inner hash
            for (short i=0; i<key_length; i++){
                data[i]= (byte) (key[(short)(key_offset+i)] ^ (0x36));
            }
            Util.arrayFillNonAtomic(data, key_length, (short)(BLOCKSIZE-key_length), (byte)0x36);
            Util.arrayCopyNonAtomic(message, message_offset, data, BLOCKSIZE, message_length);
            sha512.reset();
            sha512.doFinal(data, (short)0, (short)(BLOCKSIZE+message_length), data, BLOCKSIZE);

            // compute outer hash
            for (short i=0; i<key_length; i++){
                data[i]= (byte) (key[(short)(key_offset+i)] ^ (0x5c));
            }
            Util.arrayFillNonAtomic(data, key_length, (short)(BLOCKSIZE-key_length), (byte)0x5c);
            sha512.reset();
            sha512.doFinal(data, (short)0, (short)(BLOCKSIZE+HASHSIZE), mac, mac_offset);
            return HASHSIZE;
        } finally {
            // This buffer contains HMAC pads, message material and the intermediate digest.
            Util.arrayFillNonAtomic(data, (short)0, (short)(BLOCKSIZE + HASHSIZE), (byte)0);
        }
    }

    /** Computes SHA-512 using the digest engine already allocated during applet installation. */
    public static short computeSha512(byte[] message, short message_offset, short message_length,
            byte[] digest, short digest_offset) {
        if (sha512 == null) {
            ISOException.throwIt(Satochip.SW_UNSUPPORTED_FEATURE);
        }
        sha512.reset();
        return sha512.doFinal(message, message_offset, message_length, digest, digest_offset);
    }

}
