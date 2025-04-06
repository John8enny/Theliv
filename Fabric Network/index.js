const express = require('express');
const { spawn } = require('child_process');
const app = express();
const port = 3000;

app.use(express.json());

// Helper function to execute Fabric commands using spawn
const executeFabricCommand = (commandArgs) => {
  return new Promise((resolve, reject) => {
    console.log(`Executing command: fablo chaincode invoke ${commandArgs.join(' ')}`);

    const fabricProcess = spawn('fablo', ['chaincode', 'invoke', ...commandArgs], {
      shell: true,
      env: process.env,
    });

    let stdoutData = '';
    let stderrData = '';

    fabricProcess.stdout.on('data', (data) => {
      stdoutData += data.toString();
    });

    fabricProcess.stderr.on('data', (data) => {
      stderrData += data.toString();
    });

    fabricProcess.on('close', (code) => {
      if (code !== 0) {
        console.error(`Error details: ${stderrData || 'No stderr output'}`);
        console.error(`Exit code: ${code}`);
        reject(`Command failed with exit code ${code}: ${stderrData || 'Unknown error'}`);
      } else {
        console.log(`Command output: ${stdoutData}`);
        resolve(stdoutData);
      }
    });
  });
};

// Add Evidence
app.post('/evidence/add', async (req, res) => {
  try {
    const {
      id, cid, fileHash, evdName, caseNum, description, fileType, metadata, customData, addedByDjango
    } = req.body;

    // Required fields validation
    if (!id || !cid || !fileHash || !evdName || !caseNum || !description || !fileType || !metadata || !addedByDjango) {
      return res.status(400).json({ error: 'All fields except customData are required' });
    }

    // Args in the exact order as the chaincode's AddEvidence function
    const args = JSON.stringify({
      Args: [
        "AddEvidence",
        id,           // ID
        cid,          // CID
        fileHash,     // FileHash
        evdName,      // EvdName
        caseNum,      // CaseNum
        description,  // Description
        fileType,     // FileType
        metadata,  // Metadata (serialized as JSON string)
        customData || "",          // CustomData (optional, default to empty string if not provided)
        addedByDjango // AddedByDjango
      ]
    });

    const commandArgs = [
      '"peer0.police.example.com"',
      '"ch1"',
      '"addevidence-ch1"',
      `'${args}'`
    ];

    const result = await executeFabricCommand(commandArgs);
    res.status(200).json({ message: 'Evidence added successfully', result });
  } catch (error) {
    res.status(500).json({ error: error.toString() });
  }
});

// Get Evidence
app.get('/evidence/:evidenceId', async (req, res) => {
  try {
    const { evidenceId } = req.params;
    const args = JSON.stringify({ Args: ["GetEvidence", evidenceId] });
    const commandArgs = [
      '"peer0.police.example.com"',
      '"ch1"',
      '"addevidence-ch1"',
      `'${args}'`
    ];

    const result = await executeFabricCommand(commandArgs);
    res.status(200).json({ message: 'Evidence retrieved successfully', result });
  } catch (error) {
    res.status(500).json({ error: error.toString() });
  }
});

// Transfer Evidence
app.post('/evidence/transfer', async (req, res) => {
  try {
    const { evidenceId, newOwnerDjango } = req.body;

    if (!evidenceId || !newOwnerDjango) {
      return res.status(400).json({ error: 'evidenceId and newOwnerDjango are required' });
    }

    const args = JSON.stringify({
      Args: ["TransferEvidence", evidenceId, newOwnerDjango]
    });

    const commandArgs = [
      '"peer0.police.example.com"',
      '"ch1"',
      '"addevidence-ch1"',
      `'${args}'`
    ];

    const result = await executeFabricCommand(commandArgs);
    res.status(200).json({ message: 'Evidence transferred successfully', result });
  } catch (error) {
    res.status(500).json({ error: error.toString() });
  }
});

// Get Evidence History
app.get('/evidence/history/:evidenceId', async (req, res) => {
  try {
    const { evidenceId } = req.params;
    const args = JSON.stringify({ Args: ["GetEvidenceHistory", evidenceId] });
    const commandArgs = [
      '"peer0.police.example.com"',
      '"ch1"',
      '"addevidence-ch1"',
      `'${args}'`
    ];

    const result = await executeFabricCommand(commandArgs);
    res.status(200).json({ message: 'Evidence history retrieved successfully', result });
  } catch (error) {
    res.status(500).json({ error: error.toString() });
  }
});

app.listen(port, () => {
  console.log(`API running on http://localhost:${port}`);
});
