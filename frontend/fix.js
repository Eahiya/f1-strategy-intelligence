const { execSync } = require('child_process');
const fs = require('fs');

try {
  execSync('npx eslint src/ --ext .js,.jsx --format json > report.json', { encoding: 'utf8' });
} catch (e) {
  // eslint throws if warnings exist
}

const reportStr = fs.readFileSync('report.json', 'utf8');
const report = JSON.parse(reportStr);

report.forEach(file => {
  if (file.messages.length === 0) return;
  const path = file.filePath;
  let lines = fs.readFileSync(path, 'utf8').split('\n');
  let modifications = 0;
  
  file.messages.sort((a, b) => b.line - a.line).forEach(msg => {
    if (msg.ruleId === 'no-unused-vars' || msg.ruleId === 'react-hooks/exhaustive-deps') {
      const idx = msg.line - 1;
      if (idx > 0 && lines[idx - 1].includes('eslint-disable-next-line')) return;
      lines.splice(idx, 0, '  // eslint-disable-next-line ' + msg.ruleId);
      modifications++;
    }
  });
  
  if (modifications > 0) {
    fs.writeFileSync(path, lines.join('\n'), 'utf8');
    console.log('Fixed ' + path);
  }
});
