import { createHmac, createHash } from "crypto";
import bcrypt from "bcrypt";

export function cryptoService() {
  function createPepperHash() {
    const hash = createHash("sha256");
    const hex = hash.digest("hex");
    return hex;
  }

  function hashStringWithPepper(data: string) {
    const pepper = process.env.PEPPER_HASH;
    if (!pepper)
      throw new Error(
        "PEPPER_HASH not defined. Add to env file before proceeding",
      );
    const hmac = createHmac("sha256", pepper);
    const hex = hmac.update(data).digest("hex");
    return hex;
  }

  async function generateSaltAndHash(data: string, rounds = 10) {
    const salt = await bcrypt.genSalt(rounds);
    const peppered = hashStringWithPepper(data);
    const hash = await bcrypt.hash(peppered, salt);
    return { hash, salt };
  }

  return { createPepperHash, hashStringWithPepper, generateSaltAndHash };
}
