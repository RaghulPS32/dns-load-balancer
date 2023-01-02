
import {parseDomain, ParseResultType } from 'parse-domain';
import dns from 'dns'
import dgram from 'dgram'
import fs from 'fs'

const dnsPromises = dns.promises;

let domain = fs.readFileSync('log.json',{encoding:'utf8', flag:'r'});
domain = JSON.parse(domain.toString())

const fallbackServer = '8.8.8.8'
const server = dgram.createSocket('udp4')


function copyBuffer(src, offset, dst) {
  for (let i = 0; i < src.length; ++i) {
    dst.writeUInt8(src.readUInt8(i), offset + i)
  }
}

function send(client, msg, ...args) {
  console.log("SEND > ", msg, " - ", client)
  client.send(msg, ...args)
}

function resolve(msg, rinfo, rip) {
  const queryInfo = msg.slice(12)
  const response = Buffer.alloc(28 + queryInfo.length)
  let offset = 0
  const id = msg.slice(0, 2)
  copyBuffer(id, 0, response)  // Transaction ID
  offset += id.length
  response.writeUInt16BE(0x8180, offset)  // Flags
  offset += 2
  response.writeUInt16BE(1, offset)  // Questions
  offset += 2
  response.writeUInt16BE(1, offset)  // Answer RRs
  offset += 2
  response.writeUInt32BE(0, offset)  // Authority RRs & Additional RRs
  offset += 4
  copyBuffer(queryInfo, offset, response)
  offset += queryInfo.length
  response.writeUInt16BE(0xC00C, offset)  // offset to domain name
  offset += 2
  const typeAndClass = msg.slice(msg.length - 4)
  copyBuffer(typeAndClass, offset, response)
  offset += typeAndClass.length
  response.writeUInt32BE(600, offset)  // TTL, in seconds
  offset += 4
  response.writeUInt16BE(4, offset)  // Length of IP
  offset += 2
  rip.split('.').forEach(value => {
    response.writeUInt8(parseInt(value), offset)
    offset += 1
  })
  
  send(server, response, rinfo.port, rinfo.address, (err) => {
    if (err) {
      console.log(err)
      server.close()
    }
  })
}

function forward(msg, rinfo) {
  
  
  const client = dgram.createSocket('udp4')
  client.on('error', (err) => {
    console.log(`client error:\n${err.stack}`)
    client.close()
  })
  client.on('message', (fbMsg, fbRinfo) => {
    server.send(fbMsg, rinfo.port, rinfo.address, (err) => {
      err && console.log(err)
    })
    client.close()
  })

  send(client, msg, 53, fallbackServer, (err) => {
    if (err) {
      console.log(err)
      client.close()
    }
    
  })
}

function parseHost(msg) {
  let num = msg.readUInt8(0)
  let offset = 1
  let host = ""
  while (num !== 0) {
    host += msg.slice(offset, offset + num).toString()
    offset += num
    num = msg.readUInt8(offset)
    offset += 1
    if (num !== 0) {
      host += '.'
    }
  }
  return host
}

/*server.on('message', function(msg, rinfo) {
  console.log('Received %d bytes from %s:%d.\nMessage:%s\n',
              msg.length, rinfo.address, rinfo.port, msg);
  const sp = msg.split(",")
  msg = sp[3].toString()
  rinfo.address = sp[0].split("(")[1]
  rinfo.port = s[1].split(")")[0]
  console.log('Received %d bytes from %s:%d.\nMessage:%s\n',
              msg.length, rinfo.address, rinfo.port, msg);
  
});*/


server.on('message', async (msg, rinfo) => {
  
  let host = parseHost(msg.slice(12))
  console.log(`receive query: ${host}`)

  if (host.indexOf("." != -1) && false) {
    const parseResult = parseDomain(
      host,
    );
    host = parseResult.domain;
  }
  console.log("HOST", host, domain[host])
  try{
  if (domain[host]!==undefined) {
    //console.log(host)
    resolve(msg, rinfo, domain[host])
  }

  else {
      let r = await dnsPromises.lookup(host).catch((e) => {
      console.error("DNS Query error: ", e);
      forward(msg, rinfo,host)
    })
    
    try{
    console.log("LOOKUP DONE.", r, r.address)
    domain[host] = r.address
    resolve(msg, rinfo, r.address)
    const data = JSON.stringify(domain);

    fs.writeFile('log.json', data, (err) => {
      if (err) {
          throw err;
      }
      console.log("JSON data is saved.");
    });
    
    }
    catch(e)
    {
      console.log("couldn't resolve on own!!");
      forward(msg.rinfo);
    }

// write JSON string to a file

  }
}
catch(e)
  {
    console.log("Something Happened!!");
  }
  console.log("DONE...");
  
})

server.on('error', (err) => {
  console.log(`server error:\n${err.stack}`)
  server.close()
})

server.on('listening', () => {
  const address = server.address()
  console.log(`server listening ${address.address}:${address.port}`)
})


server.bind(57,'127.0.0.1')
